import sys
from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit


from action import CheckGrid
from action import TL01_Fighting
from action import Count
from action import DailyTask

# 获取当前工作目录
'''
resource = Resource()
resource.set_cpu()
resource_path = f"{parent_dir}/resource"
assets_resource_path = f"{parent_dir}/assets/resource"

# 检查路径是否存在，如果存在再绑定
if os.path.exists(resource_path):
    resource.post_bundle(resource_path).wait()

if os.path.exists(assets_resource_path):
    resource.post_bundle(assets_resource_path).wait()
'''


if __name__ == "__main__":
    Toolkit.init_option("./")
    if len(sys.argv) > 1:
        print("use socket_id: " + sys.argv[-1])
        socket_id = sys.argv[-1]
    else:
        print("Use Default socket_id: MAA_AGENT_SOCKET")
        socket_id = "MAA_AGENT_SOCKET"
    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()