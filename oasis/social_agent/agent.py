# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from __future__ import annotations

import inspect
import json
import logging
import re
import sys
from datetime import datetime
from typing import TYPE_CHECKING, Any

from camel.configs import ChatGPTConfig,QwenConfig
from camel.memories import (ChatHistoryMemory, MemoryRecord,
                            ScoreBasedContextCreator)
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType, OpenAIBackendRole
from camel.utils import OpenAITokenCounter

from oasis.social_agent.agent_action import SocialAction
from oasis.social_agent.agent_environment import SocialEnvironment
from oasis.social_platform import Channel
from oasis.social_platform.config import UserInfo

if TYPE_CHECKING:
    from oasis.social_agent import AgentGraph

if "sphinx" not in sys.modules:
    agent_log = logging.getLogger(name="social.agent")
    agent_log.setLevel("DEBUG")
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_handler = logging.FileHandler(f"./log/social.agent-{str(now)}.log",encoding='utf-8')
    file_handler.setLevel("DEBUG")
    file_handler.setFormatter(
        logging.Formatter(
            "%(levelname)s - %(asctime)s - %(name)s - %(message)s"))
    agent_log.addHandler(file_handler)

def extract_json_from_string(mixed_str):

    pattern = r'(\{.*?\[.*?\].*?\})'
    matches = re.findall(pattern, mixed_str, flags=re.DOTALL)

    valid_jsons = None
    for match in matches:
        try:
            valid_jsons = json.loads(match)

        except json.JSONDecodeError:
            print("无效的JSON字符串:", match)
            pass  # 忽略无效的JSON
    return valid_jsons

class SocialAgent:
    r"""Social Agent."""

    def __init__(
        self,
        agent_id: int,
        user_info: UserInfo,
        twitter_channel: Channel,
        inference_channel: Channel = None,
        model_type: str = "llama-3",
        agent_graph: "AgentGraph" = None,
        action_space_prompt: str = None,
        is_openai_model: bool = False,
    ):
        self.agent_id = agent_id
        self.user_info = user_info
        self.twitter_channel = twitter_channel
        self.infe_channel = inference_channel
        self.env = SocialEnvironment(SocialAction(agent_id, twitter_channel))
        self.system_message = BaseMessage.make_assistant_message(
            role_name="User",
            content=self.user_info.to_system_message(action_space_prompt),
        )
        self.model_type = model_type
        self.is_deepseek_chat = model_type == "deepseek-chat"
        self.is_openai_model = is_openai_model
        if self.is_openai_model:
            model_config = QwenConfig(
                tools=self.env.action.get_openai_function_list(),
                temperature=0.5,
            )
            self.model_backend = ModelFactory.create(
                model_platform=ModelPlatformType.QWEN,
                model_type=ModelType(model_type),
                model_config_dict=model_config.as_dict(),
            )

        context_creator = ScoreBasedContextCreator(
            OpenAITokenCounter(ModelType.QWEN_2_5_14B),
            4096,
        )
        self.memory = ChatHistoryMemory(context_creator, window_size=5)
        self.system_message = BaseMessage.make_assistant_message(
            role_name="system",
            content=self.user_info.to_system_message(
                action_space_prompt),  # system prompt
        )
        self.agent_graph = agent_graph
        self.test_prompt = (
            "\n"
            "Helen is a successful writer who usually writes popular western "
            "novels. Now, she has an idea for a new novel that could really "
            "make a big impact. If it works out, it could greatly "
            "improve her career. But if it fails, she will have spent "
            "a lot of time and effort for nothing.\n"
            "\n"
            "What do you think Helen should do?")

    async def perform_action_by_llm(self):
        # Get posts:
        env_prompt = await self.env.to_text_prompt()
        user_msg = BaseMessage.make_user_message(
            role_name="User",
            # content=(
            #     f"Please perform social media actions after observing the "
            #     f"platform environments. Notice that don't limit your "
            #     f"actions for example to just like the posts. "
            #     f"Here is your social media environment: {env_prompt}"),
            content=(
                f"Please perform social media actions after observing the "
                f"platform environments. "
                f"Here is your social media environment: {env_prompt}"),
        )
        self.memory.write_record(
            MemoryRecord(
                message=user_msg,
                role_at_backend=OpenAIBackendRole.USER,
            ))

        openai_messages, _ = self.memory.get_context()
        content = ""
        # sometimes self.memory.get_context() would lose system prompt
        if not openai_messages:
            openai_messages = [{
                "role": self.system_message.role_name,
                "content": self.system_message.content,
            }] + [user_msg.to_openai_user_message()]
        start_message = openai_messages[0]
        if start_message["role"] != self.system_message.role_name:
            openai_messages = [{
                "role": self.system_message.role_name,
                "content": self.system_message.content,
            }] + openai_messages


        agent_log.info(
            f"Agent {self.agent_id} is running with prompt: {openai_messages}")

        if self.is_openai_model:
            try:
                response = self.model_backend.run(openai_messages)
                agent_log.info(f"Agent {self.agent_id} response: {response}")
                content = response.choices[0].message.content
                json_content = extract_json_from_string(content)
                for function in json_content["functions"]:
                    action_name = function['name']
                    args = function['arguments']
                    print(f"Agent {self.agent_id} is performing "
                          f"action: {action_name} with args: {args}")
                    await getattr(self.env.action, action_name)(**args)
                    if self.agent_graph is not None:
                        self.perform_agent_graph_action(action_name, args)
            except Exception as e:
                print(e)
                content = "No response."

        else:
            retry = 5
            exec_functions = []

            while retry > 0:
                start_message = openai_messages[0]
                if start_message["role"] != self.system_message.role_name:
                    openai_messages = [{
                        "role": self.system_message.role_name,
                        "content": self.system_message.content,
                    }] + openai_messages
                mes_id = await self.infe_channel.write_to_receive_queue(
                    openai_messages)
                mes_id, content = await self.infe_channel.read_from_send_queue(
                    mes_id)
                if self.is_deepseek_chat and content != "No response.":
                    try:
                        content = content.split("</think>")[1]
                    except IndexError:
                        pass
                try:
                    content_json = extract_json_from_string(content)
                    agent_log.info(
                        f"Agent {self.agent_id} receive response: {content_json}")
                    functions = content_json["functions"]
                    # reason = content_json["reason"]

                    for function in functions:
                        name = function["name"]
                        # arguments = function['arguments']
                        if name != "do_nothing":
                            arguments = function["arguments"]
                        else:
                            # The success rate of do_nothing is very low
                            # It often drops the argument, causing retries
                            # It's a waste of time, manually compensating here
                            arguments = {}
                        exec_functions.append({
                            "name": name,
                            "arguments": arguments
                        })
                        if self.agent_graph is not None:
                            self.perform_agent_graph_action(name, arguments)
                    break
                except Exception as e:
                    agent_log.error(f"Agent {self.agent_id} error: {e}")
                    exec_functions = []
                    retry -= 1
            for function in exec_functions:
                try:
                    await getattr(self.env.action,
                                  function["name"])(**function["arguments"])
                except Exception as e:
                    agent_log.error(f"Agent {self.agent_id} error: {e}")
                    retry -= 1

            if retry == 0:
                content = "No response."
        agent_msg = BaseMessage.make_assistant_message(role_name="Assistant",
                                                       content=content)
        self.memory.write_record(
            MemoryRecord(message=agent_msg,
                         role_at_backend=OpenAIBackendRole.ASSISTANT))

    async def perform_test(self):
        """
        doing survey for core agents.
        """
        # user conduct test to agent
        # user_msg = BaseMessage.make_user_message(role_name="User",
        #                                   content=(self.test_prompt))
        # TODO error occurs
        # self.memory.write_record(MemoryRecord(message=user_msg,
        #                                       role_at_backend=OpenAIBackendRole.USER))

        openai_messages, num_tokens = self.memory.get_context()

        system_message_content =  self.system_message.content.split("# RESPONSE FORMAT")[0].split("# SELF-DESCRIPTION")[1]

        openai_messages = ([{
            "role":
            self.system_message.role_name,
            "content":
            "You are a twitter user." + system_message_content,
        }] + openai_messages + [{
            "role": "user",
            "content": self.test_prompt
        }])
        agent_log.info(f"Agent {self.agent_id}'s prompt: {openai_messages}")
        if self.is_openai_model:
            try:
                response = self.model_backend.run(openai_messages)
                content = response.choices[0].message.content
            except Exception as e:
                print(e)
                content = "No response."
        else:
            try:
                message_id = await self.infe_channel.write_to_receive_queue(
                    openai_messages)
                message_id, content = await self.infe_channel.read_from_send_queue(
                    message_id)
            except Exception as e:
                print(e)
                content = "No response."
        if self.is_deepseek_chat and content != "No response.":
            try:
                content = content.split("</think>")[1]
            except IndexError:
                pass
        agent_log.info(f"Agent {self.agent_id} receive response: {[content]}")
        return {
            "user_id": self.agent_id,
            "prompt": openai_messages,
            "content": content
        }

    async def perform_action_by_hci(self) -> Any:
        print("Please choose one function to perform:")
        function_list = self.env.action.get_openai_function_list()
        for i in range(len(function_list)):
            agent_log.info(f"Agent {self.agent_id} function: "
                           f"{function_list[i].func.__name__}")

        selection = int(input("Enter your choice: "))
        if not 0 <= selection < len(function_list):
            agent_log.error(f"Agent {self.agent_id} invalid input.")
            return
        func = function_list[selection].func

        params = inspect.signature(func).parameters
        args = []
        for param in params.values():
            while True:
                try:
                    value = input(f"Enter value for {param.name}: ")
                    args.append(value)
                    break
                except ValueError:
                    agent_log.error("Invalid input, please enter an integer.")

        result = await func(*args)
        return result

    async def perform_action_by_data(self, func_name, *args, **kwargs) -> Any:
        function_list = self.env.action.get_openai_function_list()
        for i in range(len(function_list)):
            if function_list[i].func.__name__ == func_name:
                func = function_list[i].func
                result = await func(*args, **kwargs)
                agent_log.info(f"Agent {self.agent_id}: {result}")
                return result
        raise ValueError(f"Function {func_name} not found in the list.")

    def perform_agent_graph_action(
        self,
        action_name: str,
        arguments: dict[str, Any],
    ):
        r"""Remove edge if action is unfollow or add edge
        if action is follow to the agent graph.
        """
        if "unfollow" in action_name:
            followee_id: int | None = arguments.get("followee_id", None)
            if followee_id is None:
                return
            self.agent_graph.remove_edge(self.agent_id, followee_id)
            agent_log.info(f"Agent {self.agent_id} unfollowed {followee_id}")
        elif "follow" in action_name:
            followee_id: int | None = arguments.get("followee_id", None)
            if followee_id is None:
                return
            self.agent_graph.add_edge(self.agent_id, followee_id)
            agent_log.info(f"Agent {self.agent_id} followed {followee_id}")

    def __str__(self) -> str:
        return (f"{self.__class__.__name__}(agent_id={self.agent_id}, "
                f"model_type={self.model_type.value})")
