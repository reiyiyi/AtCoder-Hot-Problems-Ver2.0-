from django.db import models

# Create your models here.
class Problem(models.Model):
    problem_id = models.CharField('問題ID', max_length=255, unique=True)
    problem_name = models.CharField('問題名', max_length=255)
    contest_id = models.CharField('コンテストID',max_length=255)
    contest_name = models.CharField('コンテスト名',max_length=255)

    def __str__(self):
        return 'コンテスト名:{} 問題名:{}'.format(self.contest_name, self.problem_name)

class Submission(models.Model):
    submission_id = models.CharField('提出ID', max_length=255, unique=True)
    problem = models.ForeignKey(Problem, verbose_name='問題', on_delete=models.PROTECT)
    submitter_accepted = models.IntegerField('提出者AC数')
    submitted_at = models.DateTimeField('提出日時')

    def __str__(self):
        return '問題名:{} 提出者AC数:{}　時刻:{}'.format(self.problem.problem_name, self.submitter_accepted, self.submitted_at)