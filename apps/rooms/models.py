from django.db import models

class Room(models.Model):
    TYPE_CHOICES = (
        ("silent", "静音区"),
        ("normal", "普通区"),
        ("discussion", "讨论区"),
        ("computer", "电脑区"),
    )
    STATUS_CHOICES = (
        ("open", "开放"),
        ("closed", "关闭"),
        ("maintenance", "维护中"),
    )

    name = models.CharField("自习室名称", max_length=100)
    building = models.CharField("所属建筑", max_length=100)
    floor = models.IntegerField("楼层")
    capacity = models.IntegerField("总座位数", default=0)
    room_type = models.CharField("区域类型", max_length=20, choices=TYPE_CHOICES, default="normal")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="open")
    description = models.TextField("描述", blank=True, default="")
    image = models.ImageField("图片", upload_to="rooms/", blank=True)
    open_time = models.TimeField("每日开放时间", null=True, blank=True)
    close_time = models.TimeField("每日关闭时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_room"
        verbose_name = "自习室"
        verbose_name_plural = verbose_name
        ordering = ["building", "floor", "name"]

    def __str__(self):
        return f"{self.building}{self.floor}F-{self.name}"


class Seat(models.Model):
    TYPE_CHOICES = (
        ("normal", "普通座"),
        ("power", "带电源座"),
        ("booth", "卡座"),
        ("standing", "站立桌"),
    )
    STATUS_CHOICES = (
        ("available", "可用"),
        ("maintenance", "维修中"),
        ("reserved", "预留"),
    )

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="seats", verbose_name="所属自习室")
    seat_number = models.CharField("座位编号", max_length=20)
    row = models.IntegerField("网格行", default=0)
    col = models.IntegerField("网格列", default=0)
    seat_type = models.CharField("座位类型", max_length=20, choices=TYPE_CHOICES, default="normal")
    tags = models.JSONField("设施标签", default=list, blank=True)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="available")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_seat"
        verbose_name = "座位"
        verbose_name_plural = verbose_name
        unique_together = [("room", "seat_number")]
        ordering = ["room", "row", "col"]

    def __str__(self):
        return f"{self.room.name}-{self.seat_number}"


class TimeSlot(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="timeslots",
                             verbose_name="所属自习室", null=True, blank=True)
    name = models.CharField("时段名称", max_length=50)
    start_time = models.TimeField("开始时间")
    end_time = models.TimeField("结束时间")
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        db_table = "bs_timeslot"
        verbose_name = "时段模板"
        verbose_name_plural = verbose_name
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.name}({self.start_time}-{self.end_time})"


class SpecialSchedule(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="special_schedules", verbose_name="自习室")
    date = models.DateField("日期")
    open_time = models.TimeField("开放时间", null=True, blank=True)
    close_time = models.TimeField("关闭时间", null=True, blank=True)
    is_closed = models.BooleanField("全天闭馆", default=False)
    reason = models.CharField("原因", max_length=200, blank=True, default="")

    class Meta:
        db_table = "bs_special_schedule"
        verbose_name = "特殊日程"
        verbose_name_plural = verbose_name
        unique_together = [("room", "date")]
