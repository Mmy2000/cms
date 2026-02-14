from rest_framework import serializers
from stamps.models import Company, Sector, StampCalculation, ExpectedStamp


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name"]


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ["id", "name"]


class StampCalculationSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    new_company_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Provide this OR company to auto-create a new company.",
    )

    class Meta:
        model = StampCalculation
        fields = [
            "id",
            "company",
            "company_name",
            "new_company_name",
            "value_of_work",
            "invoice_copies",
            "invoice_date",
            "stamp_rate",
            "exchange_rate",
            "d1",
            "total_past_years",
            "total_stamp_for_company",
            "note",
            "created_at",
        ]
        read_only_fields = [
            "d1",
            "total_past_years",
            "total_stamp_for_company",
            "created_at",
        ]
        extra_kwargs = {
            "company": {"required": False, "allow_null": True},
        }

    def validate(self, attrs):
        company = attrs.get("company")
        new_company_name = attrs.get("new_company_name", "").strip()
        if not company and not new_company_name:
            raise serializers.ValidationError(
                "Either 'company' or 'new_company_name' must be provided."
            )
        return attrs

    def create(self, validated_data):
        from stamps.services.stamp.stamp_service import StampService

        new_company_name = validated_data.pop("new_company_name", "").strip()
        company = validated_data.pop("company", None)
        user = self.context["request"].user

        if new_company_name:
            company, _ = Company.objects.get_or_create(
                name__iexact=new_company_name, defaults={"name": new_company_name}
            )

        if not company:
            raise serializers.ValidationError("Could not resolve company.")

        stamp = StampCalculation(**validated_data)
        stamp.company = company
        # stamp.user = user
        stamp.save()
        return stamp


class StampCalculationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = StampCalculation
        fields = [
            "id",
            "company",
            "company_name",
            "value_of_work",
            "invoice_copies",
            "invoice_date",
            "d1",
            "total_stamp_for_company",
            "created_at",
        ]


class ExpectedStampSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source="sector.name", read_only=True)
    new_sector_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Provide this OR sector to auto-create a new sector.",
    )

    class Meta:
        model = ExpectedStamp
        fields = [
            "id",
            "sector",
            "sector_name",
            "new_sector_name",
            "value_of_work",
            "invoice_copies",
            "invoice_date",
            "stamp_rate",
            "exchange_rate",
            "d1",
            "total_past_years",
            "total_stamp_for_company",
            "note",
            "created_at",
        ]
        read_only_fields = [
            "d1",
            "total_past_years",
            "total_stamp_for_company",
            "created_at",
        ]
        extra_kwargs = {
            "sector": {"required": False, "allow_null": True},
        }

    def validate(self, attrs):
        sector = attrs.get("sector")
        new_sector_name = attrs.get("new_sector_name", "").strip()
        if not sector and not new_sector_name:
            raise serializers.ValidationError(
                "Either 'sector' or 'new_sector_name' must be provided."
            )
        return attrs

    def create(self, validated_data):
        new_sector_name = validated_data.pop("new_sector_name", "").strip()
        sector = validated_data.pop("sector", None)
        user = self.context["request"].user

        if new_sector_name:
            sector, _ = Sector.objects.get_or_create(
                name__iexact=new_sector_name, defaults={"name": new_sector_name}
            )

        if not sector:
            raise serializers.ValidationError("Could not resolve sector.")

        stamp = ExpectedStamp(**validated_data)
        stamp.sector = sector
        # stamp.user = user
        stamp.save()
        return stamp


class ExpectedStampListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    sector_name = serializers.CharField(source="sector.name", read_only=True)

    class Meta:
        model = ExpectedStamp
        fields = [
            "id",
            "sector",
            "sector_name",
            "value_of_work",
            "invoice_copies",
            "invoice_date",
            "d1",
            "total_stamp_for_company",
            "created_at",
        ]
