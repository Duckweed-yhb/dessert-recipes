import os
import re
import frontmatter
from datetime import datetime
from pathlib import Path

# 1. 解析recipes目录下的所有食谱文件
recipes = []
recipes_dir = Path("recipes")
cover_dir = Path("images/cover")
latest_recipe = None
latest_cover_image = None

# 支持的图片格式
image_extensions = ['.jpg', '.jpeg', '.png', '.webp']

for md_file in sorted(recipes_dir.glob("*.md"), key=os.path.getmtime, reverse=True):
    if md_file.name == ".gitkeep":
        continue
    try:
        post = frontmatter.load(md_file)
        recipe_name = md_file.stem
        recipe = {
            "name": post.get("name", "未知"),
            "type": post.get("type", "未知"),
            "difficulty": post.get("difficulty", "未知"),
            "time": post.get("time", "未知"),
            "update_time": post.get("update_time", datetime.fromtimestamp(os.path.getmtime(md_file)).strftime("%Y-%m-%d")),
            "filename": recipe_name
        }
        recipes.append(recipe)

        # 查找最新食谱对应的封面图
        if not latest_recipe:
            latest_recipe = recipe
            for ext in image_extensions:
                cover_image_path = cover_dir / f"{recipe_name}{ext}"
                if cover_image_path.exists():
                    latest_cover_image = cover_image_path
                    break

    except Exception as e:
        print(f"解析文件 {md_file} 出错: {e}")

# 2. 生成食谱目录表格
if recipes:
    recipes_table = "| 甜点类型 | 名称 | 难度 | 制作时长 |\n"
    recipes_table += "|----------|------|------|----------|\n"
    for r in recipes:
        recipes_table += f"| {r['type']} | {r['name']} | {r['difficulty']} | {r['time']} |\n"
else:
    recipes_table = "| 甜点类型 | 名称 | 难度 | 制作时长 |\n|----------|------|------|----------|\n| 暂无     | 暂无 | 暂无 | 暂无     |\n"

# 3. 生成最近更新记录
if recipes:
    sorted_recipes = sorted(recipes, key=lambda x: x['update_time'], reverse=True)
    updates = []
    for r in sorted_recipes[:5]: # 只显示最近5条
        updates.append(f"- {r['update_time']}：新增「{r['name']}」制作教程")
    updates_str = "\n".join(updates)
else:
    updates_str = "- 暂无更新记录"

# 4. 生成仓库结构
def generate_tree(dir_path, prefix=""):
    tree = []
    items = sorted(os.listdir(dir_path))
    for i, item in enumerate(items):
        if item.startswith(".git") or item == "__pycache__":
            continue
        path = os.path.join(dir_path, item)
        is_last = i == len(items) - 1
        symbol = "└── " if is_last else "├── "
        if os.path.isdir(path):
            tree.append(f"{prefix}{symbol}{item}/          # {get_dir_desc(item)}")
            new_prefix = prefix + ("    " if is_last else "│   ")
            tree.extend(generate_tree(path, new_prefix))
        else:
            if not item.endswith(".py"): # 排除临时生成的py文件
                tree.append(f"{prefix}{symbol}{item}")
    return tree

def get_dir_desc(dir_name):
    desc_map = {
        "images": "甜点成品/过程图片",
        "cover": "封面图",
        "recipes": "详细教程文档",
        ".github": "GitHub配置文件",
        "workflows": "Actions工作流配置"
    }
    return desc_map.get(dir_name, "")

structure_lines = generate_tree(".")
structure_lines.insert(0, "dessert-recipes/")
structure_str = "```\n" + "\n".join(structure_lines) + "\n```"

# 5. 生成封面图链接
if latest_cover_image:
    # 构建GitHub Raw链接
    repo_url = os.getenv("GITHUB_REPOSITORY", "你的用户名/你的仓库名")
    cover_url = f"https://github.com/{repo_url}/raw/main/{latest_cover_image}"
    cover_markdown = f"![最新甜点封面]({cover_url})"
else:
    cover_markdown = "![甜点封面图](https://placehold.co/1200x400/e8f4f8/6c757d?text=No+Cover+Yet)"

# 6. 更新README.md
with open("README.md", "r", encoding="utf-8") as f:
    readme_content = f.read()

# 替换封面图
readme_content = re.sub(
    r'<!-- AUTO-GENERATED-COVER:START -->[\s\S]*?<!-- AUTO-GENERATED-COVER:END -->',
    f'<!-- AUTO-GENERATED-COVER:START -->\n{cover_markdown}\n<!-- AUTO-GENERATED-COVER:END -->',
    readme_content
)

# 替换食谱目录
readme_content = re.sub(
    r'<!-- AUTO-GENERATED-RECIPES:START -->[\s\S]*?<!-- AUTO-GENERATED-RECIPES:END -->',
    f'<!-- AUTO-GENERATED-RECIPES:START -->\n{recipes_table}<!-- AUTO-GENERATED-RECIPES:END -->',
    readme_content
)

# 替换最近更新
readme_content = re.sub(
    r'<!-- AUTO-GENERATED-UPDATES:START -->[\s\S]*?<!-- AUTO-GENERATED-UPDATES:END -->',
    f'<!-- AUTO-GENERATED-UPDATES:START -->\n{updates_str}\n<!-- AUTO-GENERATED-UPDATES:END -->',
    readme_content
)

# 替换仓库结构
readme_content = re.sub(
    r'<!-- AUTO-GENERATED-STRUCTURE:START -->[\s\S]*?<!-- AUTO-GENERATED-STRUCTURE:END -->',
    f'<!-- AUTO-GENERATED-STRUCTURE:START -->\n{structure_str}\n<!-- AUTO-GENERATED-STRUCTURE:END -->',
    readme_content
)

# 保存更新后的README
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme_content)

print("README更新完成！")