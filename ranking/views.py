from django.views import generic
from django.db.models import Count
from ranking.models import Submission
from django.utils import timezone
import datetime

# Create your views here.
class RankingList(generic.ListView):
    model = Submission
    template_name = "ranking/ranking_list.html"
    context_object_name = "ranking_list"
    ordering = "-total"
    start_period = None
    end_period = None
    submit_count = -1

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_list"] = {
            "all":"ALL",
            "0":"0～199",
            "200":"200～399",
            "400":"400～599",
            "600":"600～799",
            "800":"800～999",
            "1000":"1000～",
        }
        context["period_list"] = [str(period) for period in range(1, 31)]
        context["start_period"] = self.start_period
        context["end_period"] = self.end_period
        context["submit_count"] = self.submit_count

        return context

    def get_queryset(self):
        if self.queryset is not None:
            queryset = self.queryset
        elif self.model is not None:
            queryset = self.model.objects.all()

        FILTER_RANGE = {
            "all":{"lower":0, "upper":10000000},
            "0":{"lower":0, "upper":199},
            "200":{"lower":200, "upper":399},
            "400":{"lower":400, "upper":599},
            "600":{"lower":600, "upper":799},
            "800":{"lower":800, "upper":999},
            "1000":{"lower":1000, "upper":10000000}
        }

        filter = self.request.GET.get("filter")
        period = self.request.GET.get("period")

        # パラメータが正常かどうかを確認する
        if filter not in FILTER_RANGE:
            return self.model.objects.none()
        if not period.isdecimal():
            return self.model.objects.none()

        period = int(period)

        if period < 1 or period > 30:
            return self.model.objects.none()

        filter = FILTER_RANGE[filter]

        # AC数で絞り込み
        queryset = queryset.filter(submitter_accepted__gte=filter["lower"],
                                    submitter_accepted__lte=filter["upper"])

        # 提出時刻で絞り込み
        now_utc = timezone.now()
        now_jst = now_utc.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
        to_jst = datetime.datetime(now_jst.year, now_jst.month, now_jst.day, 0, 0, 0, 0,
                                    tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
        from_jst = to_jst - datetime.timedelta(days=period)
        queryset = queryset.filter(submitted_at__gte=from_jst,
                                    submitted_at__lt=to_jst)

        self.start_period = from_jst
        self.end_period = to_jst
        self.submit_count = queryset.count()

        # check
        print(queryset.order_by("submitted_at")[0])
        print(queryset.order_by("-submitted_at")[0])

        # 問題ごとの提出されたコード数の情報を持つquerysetを作成
        queryset = queryset.select_related().values(
            "problem",
            "problem__problem_id",
            "problem__problem_name",
            "problem__contest_id",
            "problem__contest_name"
            ).annotate(total=Count("submission_id"))
        
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
            
        # 上位100問を表示
        return queryset[:100]