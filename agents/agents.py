import dotenv

dotenv.load_dotenv()

from crewai import Crew, Agent, Task
from crewai.project import CrewBase, task, crew, agent
from .tools import firecrawl_search, tavily_search
from .models import (
    ViralBreakdown,
    ThreadCandidate,
    FinalOutput,
    Review,
    SubjectResearch,
    MemeResearch,
)


@CrewBase
class WritingCrew:

    agents_config = "config/agents.yml"
    tasks_config = "config/tasks.yml"

    @agent
    def hooksmith_agent(self):
        return Agent(
            config=self.agents_config["hooksmith_agent"],  # type: ignore[index]
        )

    @agent
    def debate_agent(self):
        return Agent(
            config=self.agents_config["debate_curator_agent"],  # type: ignore[index]
        )

    @agent
    def trend_spotter_agent(self):
        return Agent(
            config=self.agents_config["trend_spotter_agent"],  # type: ignore[index]
            tools=[tavily_search],
        )

    @agent
    def meme_crafter_agent(self):
        return Agent(
            config=self.agents_config["meme_crafter_agent"],  # type: ignore[index]
            tools=[tavily_search],
        )

    @agent
    def reply_driver_agent(self):
        return Agent(
            config=self.agents_config["reply_driver_agent"],  # type: ignore[index]
        )

    @agent
    def quality_judge_agent(self):
        return Agent(
            config=self.agents_config["quality_judge_agent"],  # type: ignore[index]
        )

    @agent
    def final_editor_agent(self):
        return Agent(
            config=self.agents_config["hooksmith_agent"],  # type: ignore[index]
        )

    @task
    def trend_research(self):
        return Task(
            config=self.tasks_config["trend_spotting_task"],  # type: ignore[index]
            output_pydantic=SubjectResearch,
        )

    @task
    def meme_research(self):
        return Task(
            config=self.tasks_config["meme_research_task"],  # type: ignore[index]
            output_pydantic=MemeResearch,
        )

    @task
    def write_thread(self):
        return Task(
            config=self.tasks_config["write_thread_task"],  # type: ignore[index]
            output_pydantic=ThreadCandidate,
        )

    @task
    def score_virality(self):
        return Task(
            config=self.tasks_config["viral_score_task"],  # type: ignore[index]
            output_pydantic=ViralBreakdown,
        )

    @task
    def review_and_judge(self):
        return Task(
            config=self.tasks_config["review_and_judge_task"],  # type: ignore[index]
            output_pydantic=Review,
        )

    @task
    def rewrite_thread(self):
        return Task(
            config=self.tasks_config["refine_thread_task"],  # type: ignore[index]
            output_pydantic=FinalOutput,
        )

    @crew
    def crew(self):
        return Crew(
            agents=self.agents,  # type: ignore[index]
            tasks=self.tasks,  # type: ignore[index]
            verbose=True,
        )
