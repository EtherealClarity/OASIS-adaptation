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
import subprocess
import threading
import time

import requests


def check_port_open(host, port):
    while True:
        url = f"http://{host}:{port}/health"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                break
            else:
                time.sleep(0.3)
        except Exception:
            time.sleep(0.3)


if __name__ == "__main__":
    # 本机 IP 地址
    host = "0.0.0.0"
    ports = [8002,8003]
    gpus = [0,1,2,3,4,5,6,7]

    t = None

    for i, port in enumerate(ports):
        gpu_num_per_port = int(len(gpus)/len(ports))
        gpus_per_port = gpus[int(i) * gpu_num_per_port:int(i + 1) * gpu_num_per_port]
        cmd = (
            f"CUDA_VISIBLE_DEVICES={','.join([str(n) for n in gpus_per_port ])} "
            f"python -m vllm.entrypoints.openai.api_server "
            f"--model '/home/dengshisong/Projects/DeepSeek-R1-Distill-Llama-8B' "
            f"--served-model-name 'deepseek' "
            f"--tensor-parallel-size {str(gpu_num_per_port)} "
            f"--host {host} "
            f"--port {ports[i]} "
            f"--gpu-memory-utilization 0.4 "
            f"--disable-log-stats")
        t = threading.Thread(target=subprocess.run,
                             args=(cmd, ),
                             kwargs={"shell": True},
                             daemon=True)
        t.start()
        check_port_open(host, ports[i])
    t.join()
