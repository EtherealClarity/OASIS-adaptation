import re
import json
import asyncio
# async def func():
#     print(1)
#     await asyncio.sleep(2)
#     print(2)
#     return "返回值"
# async def main():
#     print("main开始")
#     # 创建协程，将协程封装到Task对象中并添加到事件循环的任务列表中，等待事件循环去执行（默认是就绪状态）。
#     # 在调用
#     task_list = [
#         asyncio.create_task(func(), name="n1"),
#         asyncio.create_task(func(), name="n2")
#     ]
#     print("main结束")
#     # 当执行某协程遇到IO操作时，会自动化切换执行其他任务。
#     # 此处的await是等待所有协程执行完毕，并将所有协程的返回值保存到done
#     # 如果设置了timeout值，则意味着此处最多等待的秒，完成的协程返回值写入到done中，未完成则写到pending中。
#     done, pending = await asyncio.wait(task_list, timeout=2)
#     print(done, pending)
# asyncio.run(main())

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

content = 'Okay, so I\'m trying to figure out what action ClaudiaCostin should take based on the given social media environment. Let me start by understanding the situation.\n\nClaudiaCostin is a professor at FGV and Harvard, a former director at the World Bank, and president of Instituto Singularidades. Her profile suggests she\'s a thoughtful, risk-averse individual who considers consequences before acting. She\'s not a risk-taker, so she probably evaluates situations carefully.\n\nLooking at the post, Helen is a writer considering writing a novel with potential for significant impact. The post is asking whether Helen should take this risk or be cautious. The options are about the minimum success probability needed and whether she should go for it or be cautious.\n\nClaudiaCostin\'s personality is risk-averse, so she might relate to the idea of being cautious. She might agree with Helen considering the odds before taking the leap. \n\nNow, considering the possible actions: do_nothing, create_post, repost, like_post, dislike_post, follow, create_comment, like_comment, dislike_comment.\n\nSince the post is about risk-taking in creativity, Claudia might want to engage with it. She could create a comment to share her thoughts. She values education and might encourage Helen to be cautious, aligning with her own risk-averse nature.\n\nSo, the best action would be to create a comment. She can express her view on the importance of evaluating risks before taking creative steps. This aligns with her profile and the content of the post.\n</think>\n\n{\n    "reason": "The post discusses the risks involved in creative endeavors, which aligns with ClaudiaCostin\'s risk-averse personality. She might agree with the idea of evaluating success probabilities before taking action. Therefore, she could create a comment to share her perspective on the importance of caution in creative endeavors.",\n    "functions": [{\n        "name": "create_comment",\n        "arguments": {\n            "post_id": 1,\n            "content": "It\'s crucial to assess the likelihood of success before embarking on such a significant creative endeavor. Caution and careful evaluation can lead to more informed decisions, which is commendable."\n        }\n    }]\n}'

extract_json_from_string(content)
