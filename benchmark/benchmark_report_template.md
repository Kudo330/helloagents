# Benchmark Report

## Basic Info
- Project: `helloagents-trip-planner`
- Benchmark Version:
- Model Version:
- App Version / Commit:
- Run Date:
- Evaluator:
- Environment:
- Notes:

## Summary
- Total Cases:
- Passed Auto Checks:
- Auto Pass Rate:
- Average End-to-End Latency:
- P95 Latency:
- Fallback Trigger Rate:
- Error Rate:

## Dataset Results

### Core-10
- Case Count:
- Auto Pass Rate:
- Average Latency:
- Average Rubric Score:
- Key Finding:

### Stress-5
- Case Count:
- Auto Pass Rate:
- Average Latency:
- Average Rubric Score:
- Key Finding:

### Fallback-3
- Case Count:
- Auto Pass Rate:
- Average Latency:
- Average Rubric Score:
- Key Finding:

## Rubric Scores

| Dimension | Avg Score | Weight | Weighted Score | Notes |
| --- | --- | --- | --- | --- |
| Constraint Adherence |  | 0.30 |  |  |
| Itinerary Reasonableness |  | 0.25 |  |  |
| Scenario Fitness |  | 0.20 |  |  |
| Recommendation Usefulness |  | 0.15 |  |  |
| Overall Usability |  | 0.10 |  |  |
| Total |  | 1.00 |  |  |

## Rubric Definitions

### 1. Constraint Adherence
- `1`: 多个关键约束不符合，天数、预算、交通、住宿明显偏离
- `2`: 存在关键约束偏差，结果不稳定
- `3`: 大部分约束满足，但有局部偏差
- `4`: 基本满足，只有少量非关键偏差
- `5`: 所有关键约束均满足

### 2. Itinerary Reasonableness
- `1`: 行程明显混乱，不可执行
- `2`: 结构成形，但强度或逻辑较差
- `3`: 基本可用，需用户自行修改
- `4`: 整体合理，可直接参考
- `5`: 安排自然、顺畅、执行性强

### 3. Scenario Fitness
- `1`: 输出高度模板化，与输入场景关联弱
- `2`: 略有贴合，但仍较泛化
- `3`: 基本体现预算、节奏、偏好
- `4`: 较好体现用户约束与场景特征
- `5`: 高度贴合，像为该用户定制

### 4. Recommendation Usefulness
- `1`: 推荐空泛或明显不可信
- `2`: 有少量参考价值
- `3`: 大多数推荐可参考
- `4`: 推荐较实用，可信度较高
- `5`: 推荐内容实用且有明显帮助

### 5. Overall Usability
- `1`: 不可用
- `2`: 需大幅修改
- `3`: 可作为初稿
- `4`: 基本可直接使用
- `5`: 高质量，可直接采纳

## Auto Check Results

| Check Item | Pass Rate | Notes |
| --- | --- | --- |
| Schema Parse Success |  |  |
| Required Fields Present |  |  |
| Day Count Match |  |  |
| Weather Completeness |  |  |
| Budget Completeness |  |  |
| Hotel Presence |  |  |
| Meals Presence |  |  |
| Min Attractions per Day |  |  |
| Min Meals per Day |  |  |
| Fallback Expected Match |  |  |

## Engineering Metrics

| Metric | Value | Threshold | Status | Notes |
| --- | --- | --- | --- | --- |
| API Success Rate |  | >= 95% |  |  |
| Mean Latency |  | <= 8s |  |  |
| P95 Latency |  | <= 15s |  |  |
| Fallback Trigger Rate |  | monitor |  |  |
| External Service Failure Rate |  | monitor |  |  |
| Result Page Load Success |  | >= 99% |  |  |

## Failed Cases

| Case ID | Dataset | Failure Type | Severity | Root Cause Guess | Next Action |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## Top Issues
1. 
2. 
3. 

## Per-Case Notes

### Case:
- Auto Check Result:
- Latency:
- Fallback:
- Rubric Scores:
  - Constraint Adherence:
  - Itinerary Reasonableness:
  - Scenario Fitness:
  - Recommendation Usefulness:
  - Overall Usability:
- Reviewer Comment:

### Case:
- Auto Check Result:
- Latency:
- Fallback:
- Rubric Scores:
  - Constraint Adherence:
  - Itinerary Reasonableness:
  - Scenario Fitness:
  - Recommendation Usefulness:
  - Overall Usability:
- Reviewer Comment:

## Version Comparison

| Metric | Previous | Current | Delta | Conclusion |
| --- | --- | --- | --- | --- |
| Auto Pass Rate |  |  |  |  |
| Avg Rubric Total |  |  |  |  |
| Constraint Adherence |  |  |  |  |
| Itinerary Reasonableness |  |  |  |  |
| Scenario Fitness |  |  |  |  |
| Recommendation Usefulness |  |  |  |  |
| Overall Usability |  |  |  |  |
| Mean Latency |  |  |  |  |
| P95 Latency |  |  |  |  |
| Fallback Rate |  |  |  |  |

## Release Decision
- Decision: `Pass / Pass with Risk / Fail`
- Reason:
- Must Fix Before Release:
1. 
2. 
3. 

## Next Iteration Plan
1. 
2. 
3. 
