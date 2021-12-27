from django.core.management.base import BaseCommand
from ranking.models import Problem, Submission
from django.utils import timezone
import requests
import datetime
import time

class Command(BaseCommand):
    def get_contests_json_data(self):
        api_contests_url = "https://kenkoooo.com/atcoder/resources/contests.json"
        api_contests_response = requests.get(api_contests_url)
        print("hit API...")
        time.sleep(1)
        api_contests_data = api_contests_response.json()
        contests_json_data = dict()

        # key:コンテストID, value:コンテスト名
        for contest_data in api_contests_data:
            contests_json_data[contest_data["id"]] = contest_data["title"]

        return contests_json_data

    def get_problems_json_data(self):
        api_problems_url = "https://kenkoooo.com/atcoder/resources/problems.json"
        api_problems_response = requests.get(api_problems_url)
        print("hit API...")
        time.sleep(1)
        api_problems_data = api_problems_response.json()

        return api_problems_data

    def get_ac_json_data(self):
        ac_json_data = dict()
        for i in range(5000):
            api_ac_url = "https://kenkoooo.com/atcoder/atcoder-api/v3/ac_ranking?" + f"from={i*1000}&to={(i+1)*1000}"
            api_ac_response = requests.get(api_ac_url)
            print("hit API...")
            time.sleep(1)
            api_ac_data = api_ac_response.json()
            if len(api_ac_data) == 0:
                break

            # key:ユーザー名, value:AC数
            for ac_data in api_ac_data:
                ac_json_data[ac_data["user_id"]] = ac_data["count"]

        return ac_json_data

    def get_submissions_json_data(self):
        to_unix_time = int(timezone.now().timestamp())
        from_unix_time = to_unix_time - (24 + 1) * 60 * 60
        next_from_unix_time = from_unix_time

        is_added = set()
        submissions_json_data = []
        for i in range(1000):
            api_submissions_url = "https://kenkoooo.com/atcoder/atcoder-api/v3/from/" + str(from_unix_time)
            api_submissions_response = requests.get(api_submissions_url)
            print("hit API... " + str(i+1))
            time.sleep(1)
            api_submissions_data = api_submissions_response.json()

            # 前日の追加していない提出データはまだあるか
            if len(api_submissions_data) == 0:
                break

            # 漏れなくデータを追加することができるように
            next_from_unix_time = api_submissions_data[-1]["epoch_second"]
            if from_unix_time == next_from_unix_time:
                next_from_unix_time += 1
            from_unix_time = next_from_unix_time

            for submission_data in api_submissions_data:
                if submission_data["id"] in is_added:
                    continue
                submissions_json_data.append(submission_data)
                is_added.add(submission_data["id"])

            if from_unix_time >= to_unix_time:
                break

        return submissions_json_data

    def handle(self, *args, **options):
        start = time.time()
        contests_json_data = self.get_contests_json_data()
        problems_json_data = self.get_problems_json_data()
        ac_json_data = self.get_ac_json_data()
        print("success")

        # 問題データの追加
        problems = []
        for problem_data in problems_json_data:
            # problem_idのunique制約を考慮
            if Problem.objects.filter(problem_id=problem_data["id"]).exists():
                continue
            problem = Problem(
                problem_id = problem_data["id"],
                problem_name = problem_data["title"],
                contest_id = problem_data["contest_id"],
                contest_name = contests_json_data[problem_data["contest_id"]]
            )
            problems.append(problem)

        Problem.objects.bulk_create(problems)
        print('追加された問題データ数:{}'.format(len(problems)))

        submissions_json_data = self.get_submissions_json_data()
        print("success")

        # 提出データの追加
        submissions = []
        for submission_data in submissions_json_data:
            # submission_idのunique制約を考慮
            if Submission.objects.filter(submission_id=submission_data["id"]).exists():
                continue
            # ユーザー名の変更や退会などを考慮
            if not submission_data["user_id"] in ac_json_data:
                continue
            submission = Submission(
                submission_id = submission_data["id"],
                problem = Problem.objects.get(problem_id=submission_data["problem_id"]),
                submitter_accepted = ac_json_data[submission_data["user_id"]],
                submitted_at = datetime.datetime.fromtimestamp(submission_data["epoch_second"]).astimezone()
            )
            submissions.append(submission)

        Submission.objects.bulk_create(submissions)
        print('追加された提出データ数:{}'.format(len(submissions)))

        # 古い提出データの削除
        now_utc = timezone.now()
        delete_utc = now_utc - datetime.timedelta(days=31)
        print('削除された提出データ数:{}'.format(Submission.objects.filter(submitted_at__lt=delete_utc).count()))
        Submission.objects.filter(submitted_at__lt=delete_utc).delete()

        print("complete")
        print('実行時間:{}秒'.format(time.time()-start))