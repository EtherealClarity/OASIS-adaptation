# -*- coding: utf-8 -*- 
# @Time : 2025/3/24 14:31 
# @Author : Shisong Deng
# @File : data_to_json.py

import sqlite3
import json
import datetime
import random


def format_post_datetime(created_at: int) -> str:
    """
    根据帖子时间步 (created_at)，返回一个带有随机偏差的完整日期时间字符串。
    规则：
      - 基准时间：2025-03-01 19:00:00。
      - 每个时间步代表 10 分钟累加。
      - 同时引入 ±5 分钟的随机偏差，使时间更贴近实际。
    返回示例： "7:03 PM · Mar 1, 2025"
    """
    # 基准时间：2025-03-01 19:00:00
    base_time = datetime.datetime(2025, 3, 1, 19, 0, 0)
    # 每个 time_step = 10 分钟
    step_delta = datetime.timedelta(minutes=10 * created_at)
    # 随机偏差 ±5 分钟
    random_offset = datetime.timedelta(minutes=random.randint(-5, 5))
    # 计算实际时间
    post_time = base_time + step_delta + random_offset
    # 格式化为类似 "7:00 PM"
    time_part = post_time.strftime('%I:%M %p')
    if time_part.startswith('0'):
        # 去除如 "07:03 PM" 的前导 0
        time_part = time_part[1:]

    # 日期部分 "Mar 1, 2025"
    date_part = post_time.strftime('%b %d, %Y')
    date_part = date_part.replace(' 0', ' ')
    return f"{time_part} · {date_part}"


def format_comment_datetime(created_at: int) -> str:
    """
    根据评论时间步 (created_at)，返回一个只包含月-日的日期字符串。
    规则：
      - 基准时间：2025-03-01 19:00:00
      - 每个时间步代表 10 分钟累加
      - 当时间步累加跨越24小时(144个时间步)时，自动变更日期
    返回示例： "Mar 1", "Mar 2", ...
    """
    # 基准时间：2025-03-01 19:00:00
    base_time = datetime.datetime(2025, 3, 1, 19, 0, 0)
    # 每个 time_step = 10 分钟
    step_delta = datetime.timedelta(minutes=10 * created_at)
    # 计算实际评论时间
    comment_time = base_time + step_delta
    # 仅显示 "月 日"，例如 "Mar 1"
    date_part = comment_time.strftime('%b %d')
    date_part = date_part.replace(' 0', ' ')
    return date_part


def export_twitter_data_to_json(db_path: str, output_path: str) -> None:
    """
    从数据库中读取帖子、评论、用户信息，导出为类似 Twitter 样式的 JSON 文件。
    Args:
        db_path (str): SQLite 数据库文件路径
        output_path (str): 输出的 JSON 文件路径
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1) 查询所有帖子
    cursor.execute("""
        SELECT post_id, user_id, created_at, content, num_likes, num_shares
        FROM post
        ORDER BY post_id
    """)
    posts_data = cursor.fetchall()

    def fetch_user_info(user_id: int):
        """
        根据 user_id 从 user 表获取 (name, user_name)，若不存在则返回 ("", "")。
        """
        cursor.execute("SELECT name, user_name FROM user WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if row:
            return row[0], row[1]
        return ("", "")

    all_posts = []

    # 2) 遍历帖子，将相关信息及评论一并整合
    for (post_id, post_user_id, post_created_at, post_content, post_num_likes, post_num_shares) in posts_data:
        # 发帖用户信息
        user_name, user_name_at = fetch_user_info(post_user_id)
        user_name_at_str = f"@{user_name_at}" if user_name_at else ""
        # 帖子时间
        formatted_post_time = format_post_datetime(post_created_at)

        # 3) 查找此帖子下的所有评论
        cursor.execute("""
            SELECT comment_id, user_id, content, created_at, num_likes
            FROM comment
            WHERE post_id=?
            ORDER BY comment_id
        """, (post_id,))
        comments_data = cursor.fetchall()

        comment_list = []
        for (comment_id, comment_user_id, comment_content, comment_created_at, comment_num_likes) in comments_data:
            # 评论用户信息
            c_user_name, c_user_name_at = fetch_user_info(comment_user_id)
            c_user_name_at_str = f"@{c_user_name_at}" if c_user_name_at else ""
            # 评论时间
            formatted_comment_time = format_comment_datetime(comment_created_at)
            comment_list.append({
                "评论id": comment_id,
                "评论时间": formatted_comment_time,
                "评论内容": comment_content,
                "评论用户id": comment_user_id,
                "评论用户名": c_user_name,
                "评论用户名@": c_user_name_at_str,
                "喜欢评论数量": comment_num_likes
            })

        # 4) 整合帖子信息
        post_info = {
            "帖子id": post_id,
            "发帖时间": formatted_post_time,
            "帖子内容": post_content,
            "用户id": post_user_id,
            "用户名": user_name,
            "用户名@": user_name_at_str,
            "评论数量": len(comments_data),
            "喜欢帖子数量": post_num_likes,
            "分享帖子数量": post_num_shares,
            "评论列表": comment_list
        }
        all_posts.append(post_info)

    # 5) 生成最终 JSON 结构
    final_result = {
        "帖子列表": all_posts
    }

    # 6) 写入 JSON 文件
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=4)

    conn.close()
    print(f"已完成写入: {output_path}")


def export_network_data_to_json(db_path: str, output_path: str) -> None:
    """
    从数据库中按时间步 (created_at) 读取发帖、评论、及用户互动(关注/点赞/评论/点赞评论)信息，
    并导出为网络可视化所需的 JSON 格式。
    Args:
        db_path (str): SQLite 数据库文件路径
        output_path (str): 输出的 JSON 文件路径
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1) 获取所有出现过的时间步 created_at，并排序
    tables_with_created_at = ["post", "comment", "comment_like", "like", "follow"]
    time_steps_queries = [f"SELECT DISTINCT created_at FROM {table}" for table in tables_with_created_at]
    union_query = " UNION ".join(time_steps_queries)
    cursor.execute(union_query)
    all_time_steps = sorted(row[0] for row in cursor.fetchall())

    # 2) 发帖 / 评论作者映射
    post_author_map = {}
    try:
        cursor.execute("SELECT post_id, user_id FROM post")
        for (post_id, user_id) in cursor.fetchall():
            post_author_map[post_id] = user_id
    except:
        pass

    comment_author_map = {}
    try:
        cursor.execute("SELECT comment_id, user_id, post_id FROM comment")
        for (c_id, c_user_id, c_post_id) in cursor.fetchall():
            comment_author_map[c_id] = (c_user_id, c_post_id)
    except:
        pass

    # 3) 按时间步收集信息
    iteration_list = []
    for t_step in all_time_steps:
        # 3.1 收集发帖或评论的用户 => 作为“点”
        posted_users = set()
        try:
            cursor.execute("SELECT user_id FROM post WHERE created_at=?", (t_step,))
            for (uid,) in cursor.fetchall():
                posted_users.add(uid)
        except:
            pass

        commented_users = set()
        try:
            cursor.execute("SELECT user_id FROM comment WHERE created_at=?", (t_step,))
            for (uid,) in cursor.fetchall():
                commented_users.add(uid)
        except:
            pass

        # 本时间步有行为(发帖或评论)的用户
        behavior_users = sorted(posted_users.union(commented_users))

        points = []
        for uid in behavior_users:
            points.append({
                "用户id": uid,
                "是否发帖或者评论": 1
            })

        # 3.2 收集所有在当前时间步的“边” (互动)
        edges = []

        # a) 关注
        try:
            cursor.execute("SELECT follower_id, followee_id FROM follow WHERE created_at=?", (t_step,))
            for (follower, followee) in cursor.fetchall():
                edges.append({
                    "出度id": follower,
                    "入度id": followee,
                    "互动类型": "关注"
                })
        except:
            pass

        # b) 点赞帖子
        try:
            cursor.execute("SELECT user_id, post_id FROM like WHERE created_at=?", (t_step,))
            for (liker, p_id) in cursor.fetchall():
                post_author = post_author_map.get(p_id)
                if post_author is not None:
                    edges.append({
                        "出度id": liker,
                        "入度id": post_author,
                        "互动类型": "喜欢帖子"
                    })
        except:
            pass

        # c) 评论帖子
        try:
            cursor.execute("SELECT user_id, post_id FROM comment WHERE created_at=?", (t_step,))
            for (commenter, p_id) in cursor.fetchall():
                post_author = post_author_map.get(p_id)
                if post_author is not None:
                    edges.append({
                        "出度id": commenter,
                        "入度id": post_author,
                        "互动类型": "评论"
                    })
        except:
            pass

        # d) 点赞评论
        try:
            cursor.execute("SELECT user_id, comment_id FROM comment_like WHERE created_at=?", (t_step,))
            for (comment_liker, c_id) in cursor.fetchall():
                if c_id in comment_author_map:
                    c_author, _ = comment_author_map[c_id]
                    edges.append({
                        "出度id": comment_liker,
                        "入度id": c_author,
                        "互动类型": "喜欢评论"
                    })
        except:
            pass

        # 3.3 组装当前时间步信息
        iteration_data = {
            "时间步": t_step,
            "点": points,
            "边": edges
        }
        iteration_list.append(iteration_data)

    # 4) 输出结果
    final_result = {
        "迭代信息": iteration_list
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=4)

    conn.close()
    print(f"数据提取完成，结果已写入: {output_path}")


if __name__ == "__main__":

    db_file = "D:/Social Simulation/Code322/OASIS-adaptation/data/group_polarization.db"
    network_visualization_file = "network_visualization.json"
    twitter_file = "twitter_visualization.json"

    # 导出网络可视化所需 JSON
    export_network_data_to_json(db_file, network_visualization_file)
    # 导出类似 Twitter 帖子-评论形式的 JSON
    export_twitter_data_to_json(db_file, twitter_file)

















