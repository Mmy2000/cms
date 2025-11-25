from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Company(models.Model):
    name = models.CharField(_("Company name"), max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")

    def __str__(self):
        return f"{self.name}"


class StampCalculation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="stamp_calculations",verbose_name=_("Company"))
    value_of_work = models.DecimalField(_("Value Of Work (A)"), max_digits=19, decimal_places=2)
    invoice_copies = models.PositiveIntegerField(_("Invoice Copies (B)"))
    invoice_year = models.PositiveIntegerField(_("Invoice Year"),null=True, blank=True)
    stamp_rate = models.DecimalField(_("Stamp rate (C)"), max_digits=6, decimal_places=4, default=0.0015)
    exchange_rate = models.DecimalField(_("Exchange Rate"), max_digits=10, decimal_places=4, default=1, validators=[MinValueValidator(0.0001)],help_text="سعر الصرف لتحويل القيمة إذا كانت بالعملة الأجنبية")

    d1 = models.DecimalField(_("Total stamp duty for the claim"), max_digits=19, decimal_places=2, blank=True, null=True)
    total_past_years = models.DecimalField(_("Past years total"), max_digits=19, decimal_places=2, default=0,help_text="إجمالي السنوات السابقة لنفس الشركة يتم حسابه تلقائيًا")
    total_stamp_for_company = models.DecimalField(_("Total stamp"), max_digits=19, decimal_places=2, blank=True, null=True,help_text="الإجمالي بعد جمع كل السنوات السابقة مع الحالي يتم حسابه تلقائيًا")

    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Stamp Calculation")
        verbose_name_plural = _("Stamp Calculations")

    def save(self, *args, **kwargs):
        # احسب D1
        self.d1 = self.value_of_work * self.invoice_copies * self.stamp_rate * self.exchange_rate

        # احسب كل السابق لنفس الشركة قبل إنشاء هذا السجل
        if self.pk:  
            # لو بنعمل تحديث → استثني التسجيل الحالي فقط
            past_total = (
                StampCalculation.objects
                .filter(company=self.company)
                .exclude(pk=self.pk)
                .aggregate(models.Sum("d1"))["d1__sum"] or 0
            )
        else:
            # لو أول مرة يتحفظ → اجمع كل السابق لنفس الشركة
            past_total = (
                StampCalculation.objects
                .filter(company=self.company)
                .aggregate(models.Sum("d1"))["d1__sum"] or 0
            )

        self.total_past_years = past_total

        # احسب الإجمالي
        self.total_stamp_for_company = self.d1 + self.total_past_years

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company} "
