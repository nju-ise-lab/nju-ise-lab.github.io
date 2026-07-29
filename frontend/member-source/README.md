# 成员 CSV 维护

成员介绍分为三个维护源：

- `teachers.csv`：教师；
- `phd.csv`：博士研究生；
- `masters.csv`：硕士研究生。

教师字段：

```text
id,name,avatar,member_type,identity,homepage,bio
```

博士、硕士字段：

```text
id,name,member_type,identity,homepage
```

注意：

- `id` 决定稳定个人页地址，已有成员不要修改；
- CSV 行顺序就是页面展示顺序；
- 教师头像文件放在 `frontend/content/members/<id>/`，`avatar` 只填写文件名；
- `homepage` 可留空，但填写时必须是完整的 `http://` 或 `https://` 链接；
- 教师、博士、硕士的 `member_type` 分别固定为 `teacher`、`phd`、`master`；
- 修改后从项目根目录运行 `bash scripts/build.sh`，构建会自动生成成员 JSON 和个人页。
