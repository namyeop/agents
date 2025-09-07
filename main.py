from agents.agents import WritingCrew
import os


def main():
    runner = WritingCrew()
    result = runner.crew().kickoff(
        inputs={
            "topic": "개발자의 미래에 대해 어그로를 끄는 글",
            "platform": "트위터",
            "target_audience": "20-30대 주니어 개발자",
        }
    )

    print(result)


if __name__ == "__main__":
    main()
