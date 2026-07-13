# Seoul Transit Weather Analysis
## Statistics In Python - Project 01



**Research Question**: How do inclimate weather conditions impact public transportation volume in Seoul, and how do commuters describe rainy experiences in online texts?

### Basic Requirements
Find a topic you are interested in and formulate the research question
Apply the whole pipeline of data analysis with python
Data acquisition: 
crawl large-scale data by yourself 
or you can use any published datasets directly
Study design: 
Purely descriptive statistics are not acceptable!!!
Data analysis:
Quantifying the sociopsychological dimensions with word frequency or LLMs
Apply statistical analysis, presenting the results with tables and figures
Discuss and explain your results and draw conclusions


## Setup

### Configuration File

Create a `scripts/config.py` file with your API keys:

```python
# API Configuration
# Store sensitive API keys here - add this file to .gitignore

YOUTUBE_API_KEY = "your_youtube_api_key_here"
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
DEEPSEEK_MODEL = "deepseek-v4-flash"
```

**Note:** `config.py` is included in `.gitignore` and will not be tracked by git.


## Results

### Transportation Volume Analysis

There was no statistically significant difference in public transportation volume between rainy and non-rainy days.

* T-statistic: `-0.34`
* P-value: `0.7320`

### Rainy Commuting Issues and Emotional Responses

Rainy commuting issue types and emotional responses showed a statistically significant association.

* Chi-square statistic: `21.686`
* Degrees of freedom: `9`
* P-value: `0.0099`
* Cramér’s V: `0.245`

However, 37.5% of the expected frequencies were below 5. Therefore, the chi-square result should be interpreted as exploratory.
