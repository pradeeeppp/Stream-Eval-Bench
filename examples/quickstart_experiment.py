import json
import sys
import pathlib

# Ensure stream_eval is on Python path
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from stream_eval import (
    StreamingEnvironment,
    get_usecase,
    list_usecases,
    MockAgent,
    VLMStreamingAgent,
    GradioVLMBackend,
)


def run_quickstart():
    print(f"Available UseCases: {list_usecases()}\n")

    # 1. Select a use case
    usecase = get_usecase("table_assembly_tray")
    print(f"Loaded UseCase: {usecase.name}")
    print(f"Schema: {usecase.schema}")
    print(f"Packets to stream: {[p.packet_id for p in usecase.packets]}\n")

    # 2. Select or create an agent
    # You can use MockAgent, VLMStreamingAgent(GradioVLMBackend()),
    # LocalHuggingFaceBackend, or OpenAICompatibleBackend.
    agent = MockAgent(mode="oracle")
    print(f"Using Agent: {agent.name}\n")

    # 3. Create the streaming environment with 'delayed' schedule
    env = StreamingEnvironment(usecase=usecase, schedule="delayed")

    # 4. Run full episode
    print("Running Delayed Streaming Episode...")
    episode_result = env.run_episode(agent, verbose=True)

    # 5. Review results and research metrics
    print("\nEpisode Evaluation Summary:")
    print(json.dumps(episode_result.metrics, indent=2))


if __name__ == "__main__":
    run_quickstart()
