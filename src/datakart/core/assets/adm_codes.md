# SGIS 행정구역코드
## https://sgis.kostat.go.kr/view/board/faqView?post_no=11

### CSV to JSON converter
```python
import pathlib

import pandas as pd

path = pathlib.Path(__file__).parent
df_temp = pd.read_csv(path / "adm_code_2306.csv", dtype="string")
df_drop = df_temp.drop(columns=["읍면동코드", "읍면동명칭"]).drop_duplicates()
df_drop.to_json(path / "adm_codes_2306.json", index=False, orient="records", force_ascii=False)
```
