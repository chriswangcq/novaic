# P003: 审计显式依赖边界与 side-effect adapter

## Problem
审计显式依赖边界与 side-effect adapter

## Success Criteria
- 确认 time/id/env/http/global state 是否只在边界层出现，effect adapter 是否是唯一副作用出口
