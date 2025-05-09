from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
import json

@AgentServer.custom_action("Count")
class Count(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        argv: dict = json.loads(argv.custom_action_param)
        print(argv)
        if not argv:
            return CustomAction.RunResult(success=True)
        if argv.get("count") <= argv.get("target_count"):
            argv["count"] += 1
            context.override_pipeline(
                {
                    argv.get("self"): {
                        "custom_action_param": argv,
                    },
                }
            )
            print(f"执行 {argv.get('count')} 次 TL01_Start")
            context.run_task("TL01_Start")
        else:
            context.override_pipeline(
                {
                    argv.get("self"): {
                        "custom_action_param": {
                            "self": argv.get("self"),
                            "count": 0,
                            "target_count": argv.get("target_count"),
                            "next_node": argv.get("next_node"),
                        },
                    },
                }
            )
            for i in argv.get("next_node"):
                context.run_task(i)

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("CountTask") 
class CountTask(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        argv: dict = json.loads(argv.custom_action_param)
        print(argv)
        if not argv:
            return CustomAction.RunResult(success=True)

        count = argv.get("count")
        target_count = argv.get("target_count")
        print(f"count = {count}, target_count = {target_count}")
        while count < target_count:
            print(f"excute {count} 次 TL01_Start")
            context.run_task("TL01_Start")
            count += 1

        for i in argv.get("next_node"):
            context.run_task(i)

        return CustomAction.RunResult(success=True)