from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.accounts.models import User

class SearchHistory(models.Model):
    # Người thực hiện tìm kiếm (Là "Tôi")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='search_histories'
    )

    # TRƯỜNG HỢP 1: Click vào User (Lưu ID người đó)
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='search_target_users',
        help_text="Người dùng được click vào từ kết quả tìm kiếm"
    )

    # TRƯỜNG HỢP 2: Chỉ tìm text (Lưu từ khóa)
    query = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Từ khóa tìm kiếm nếu không click vào user cụ thể"
    )

    # Thời gian tạo và cập nhật
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Quan trọng: Dùng để sort cái nào mới nhất lên đầu

    class Meta:
        # Sắp xếp mặc định: Mới xem nhất lên đầu
        ordering = ['-updated_at']
        # Đánh Index để query nhanh hơn khi bảng này to lên
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
        verbose_name = "Lịch sử tìm kiếm"
        verbose_name_plural = "Lịch sử tìm kiếm"

    def __str__(self):
        if self.target_user:
            return f"{self.user.username} viewed {self.target_user.username}"
        return f"{self.user.username} searched '{self.query}'"

    def clean(self):
        # Validation: Đảm bảo không lưu dòng rỗng (cả 2 đều null)
        if not self.target_user and not self.query:
            raise ValidationError("Phải có target_user hoặc query.")