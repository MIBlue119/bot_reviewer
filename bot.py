import openai
import os
import re
from github import Github

# Set up OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

# Set up GitHub API access
g = Github(os.environ["GITHUB_TOKEN"])
repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])

# Regular expression to match code block markdown
CODE_BLOCK_REGEX = re.compile("```([a-z]*)\n(.*?)\n```", re.DOTALL)

def get_code_from_comment(comment):
    """Extract code blocks from a GitHub comment."""
    matches = CODE_BLOCK_REGEX.findall(comment.body)
    return [match[1] for match in matches]

def generate_code_review_feedback(code_blocks):
    """Generate feedback on code using OpenAI Codex API."""
    feedback = []
    for code in code_blocks:
        prompt = f"Review this code: {code}"
        response = openai.Completion.create(
            engine="davinci-codex",
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.7,
        )
        feedback.append(response.choices[0].text)
    return feedback

# Get the pull request that triggered the bot
event_data = os.environ["GITHUB_EVENT_PATH"]
with open(event_data, "r") as f:
    event = json.load(f)
pr_number = event["pull_request"]["number"]
pr = repo.get_pull(pr_number)

# Get the code blocks from the pull request description and comments
code_blocks = [pr.body] + [comment.body for comment in pr.get_review_comments()]
code_blocks = [block for block in code_blocks if CODE_BLOCK_REGEX.search(block)]

# Generate feedback on the code
feedback = generate_code_review_feedback(code_blocks)

# Post the feedback as comments on the pull request
for comment, feedback_text in zip(pr.get_review_comments(), feedback):
    comment.create_reaction("Eyes")
    comment.create_reply(feedback_text)
