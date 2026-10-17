#!/usr/bin/env python3
"""校验 profile.yaml 是否符合 contracts/profile.schema.json 的结构。

只做「存在性」校验：必填字段在不在、列表项类型对不对。不做内容质量校验
（不打标签词表、不查 tags 拼写），避免把长期维护的素材库卡死在用词上。

零依赖设计：未安装 pyyaml 时优雅跳过（exit 0），不阻塞主流程；
安装 pyyaml 后则执行结构校验，缺失必填字段时退出码非 0。

用法: python3 check_profile.py <path/to/profile.yaml>
"""
import sys
import os

REQUIRED_TOP = ["meta", "education", "experience", "projects", "skills"]
REQUIRED_META = ["name", "phone", "email", "city"]
REQUIRED_EXPERIENCE = ["org", "role", "period", "bullets"]
REQUIRED_PROJECT = ["name", "period", "bullets"]
REQUIRED_SKILL = ["category", "items"]
REQUIRED_EDUCATION = ["school", "degree", "period"]

# 可选数组字段：仅在其出现时校验条目必填字段，缺整段不报错。
# 条目可为字符串或对象；对象必须带下列键，否则简历生成时读不到关键事实。
OPTIONAL_LIST_ITEM_REQUIRED = {
    "summary": ["text"],
    "open_source": ["name"],
    "publications": ["title"],
    "extras": ["title"],
    "attachments": ["file"],
}


def fail(msg):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        fail("用法: python3 check_profile.py <path/to/profile.yaml>")
    path = sys.argv[1]
    if not os.path.isfile(path):
        fail(f"文件不存在: {path}")

    try:
        import yaml  # noqa: F401
    except ImportError:
        print("⚠️ 未安装 pyyaml，跳过 profile 结构校验（pip install pyyaml 可启用）")
        sys.exit(0)

    import yaml
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except Exception as e:  # yaml 解析错误
            fail(f"YAML 解析失败: {e}")

    if not isinstance(data, dict):
        fail("profile.yaml 顶层必须是 mapping")

    for key in REQUIRED_TOP:
        if key not in data:
            fail(f"缺少必填顶层字段: {key}")

    meta = data.get("meta") or {}
    for key in REQUIRED_META:
        if key not in meta:
            fail(f"meta 缺少必填字段: {key}")

    for i, edu in enumerate(data.get("education") or []):
        for key in REQUIRED_EDUCATION:
            if key not in edu:
                fail(f"education[{i}] 缺少必填字段: {key}")

    for i, exp in enumerate(data.get("experience") or []):
        for key in REQUIRED_EXPERIENCE:
            if key not in exp:
                fail(f"experience[{i}] 缺少必填字段: {key}")

    for i, proj in enumerate(data.get("projects") or []):
        for key in REQUIRED_PROJECT:
            if key not in proj:
                fail(f"projects[{i}] 缺少必填字段: {key}")

    for i, sk in enumerate(data.get("skills") or []):
        for key in REQUIRED_SKILL:
            if key not in sk:
                fail(f"skills[{i}] 缺少必填字段: {key}")

    # 可选字段：出现才校验，避免为「暂时没有论文」的用户报错
    for field, req_keys in OPTIONAL_LIST_ITEM_REQUIRED.items():
        items = data.get(field)
        if items is None:
            continue
        if not isinstance(items, list):
            fail(f"{field} 必须是数组")
        for i, item in enumerate(items):
            if isinstance(item, str):
                continue
            if not isinstance(item, dict):
                fail(f"{field}[{i}] 必须是字符串或对象")
            for key in req_keys:
                if key not in item:
                    fail(f"{field}[{i}] 缺少必填字段: {key}")

    # bullets 同时支持字符串与 {text, tags} 两种写法
    for section in ("experience", "projects"):
        for i, entry in enumerate(data.get(section) or []):
            bullets = entry.get("bullets") or []
            if not isinstance(bullets, list):
                fail(f"{section}[{i}].bullets 必须是数组")
            for j, b in enumerate(bullets):
                if isinstance(b, str):
                    continue
                if not isinstance(b, dict) or "text" not in b:
                    fail(f"{section}[{i}].bullets[{j}] 必须是字符串或含 text 的对象")

    print(f"✅ profile 校验通过: {path}")


if __name__ == "__main__":
    main()
