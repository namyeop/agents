from writing_agents.agents import WritingCrew
import os


def main():
    runner = WritingCrew()
    result = runner.crew().kickoff(
        inputs={
            "topic": "대체 불가능한 사람이 되고 싶다는 커리어 목표",
            "platform": "트위터",
            "target_audience": "20-30대 주니어 개발자",
            "tone": "약간 도발적이고, 유머러스하면서, 디시인스러운",
        }
    )

    print(result)


if __name__ == "__main__":
    main()
