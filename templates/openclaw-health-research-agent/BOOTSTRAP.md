# VitaClaw Research Bootstrap

进入工作区后，默认执行以下检查清单：

1. 读取 `SOUL.md`
2. 若当前是 direct chat 或用户明确授权，读取 `MEMORY.md`
3. 读取 `memory/research/watchlist.md`
4. 如果当前任务对应某个主题，则读取 `memory/research/topics/*.md`
5. 如果已有历史摘要，则读取 `memory/research/briefs/*.md`
6. 默认不主动读取 `memory/health/daily/*.md`，除非用户明确要求研究个人纵向记录
7. 若研究结论需要回传主健康分身，再读取 `memory/health/heartbeat/preferences.md` 与 `task-board.md`
