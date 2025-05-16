import sys
from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit


from action import CheckGrid
from action import TL01_Fighting
from action import Count
from action import DailyTask
from action import CircusReward

# 获取当前工作目录

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