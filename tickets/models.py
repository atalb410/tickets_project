from django.db import models
from django.contrib.auth.models import User
import uuid

class AddOn(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Insurer(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class QuotationRequest(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Assigned', 'Assigned'),
        ('Resolved', 'Resolved'),
        ('Incomplete', 'Incomplete'),
        ('Accepted', 'Accepted'),
        ('Payment', 'Payment'),
        ('Payment Link Shared', 'Payment Link Shared'), #added
        ('Changes Requested', 'Changes Requested'),
        ('Inspection Requested', 'Inspection Requested'),
    ]

    PRODUCT_TYPES = [
        ('Private Car', 'Private Car'),
        ('PCV', 'PCV'),
        ('GCV', 'GCV'),
        ('Misc-D', 'Misc-D'),
    ]

    BUSINESS_TYPES = [
        ('New Business', 'New Business'),
        ('Renewal', 'Renewal'),
        ('Rollover', 'Rollover'),
        ('Break-In', 'Break-In'),
        ('Used', 'Used'),
    ]

    COVERAGE_TYPES = [
        ('Comprehensive', 'Comprehensive'),
        ('Third Party', 'Third Party'),
        ('SAOD', 'SAOD'),
    ]

    NCB_CHOICES = [
        ('0%', '0%'),
        ('20%', '20%'),
        ('25%', '25%'),
        ('35%', '35%'),
        ('45%', '45%'),
        ('50%', '50%'),
        ('55%', '55%'),
        ('60%', '60%'),
    ]

    CLAIM_STATUS_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]

    tracking_id = models.CharField(max_length=10, unique=True, blank=True)
    registration_number = models.CharField(max_length=20)
    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPES)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPES)
    coverage_type = models.CharField(max_length=50, choices=COVERAGE_TYPES)
    make_model_variant = models.CharField(max_length=200)
    registration_date = models.DateField(blank=True, null=True)
    add_ons = models.ManyToManyField(AddOn, blank=True)
    preferred_insurer = models.ManyToManyField(Insurer, blank=True)
    preferred_idv = models.CharField(max_length=100, blank=True)
    additional_requirements = models.TextField(blank=True)
    previous_expiry_date = models.DateField(blank=True, null=True)
    ncb = models.CharField(max_length=10, choices=NCB_CHOICES, blank=True, null=True,
                           verbose_name="No Claim Bonus")
    claim_status = models.CharField(max_length=3, choices=CLAIM_STATUS_CHOICES, blank=True, null=True,
                                    verbose_name="Previous Year Claim Status")
    rto_code = models.CharField(max_length=4, blank=True, null=True, verbose_name="RTO Code")
    document1 = models.FileField(upload_to='quotation_docs/', blank=True)
    document2 = models.FileField(upload_to='quotation_docs/', blank=True)
    document3 = models.FileField(upload_to='quotation_docs/', blank=True)
    document4 = models.FileField(upload_to='quotation_docs/', blank=True)
    document5 = models.FileField(upload_to='quotation_docs/', blank=True)
    kyc_document1 = models.FileField(upload_to='kyc_docs/', blank=True, null=True)
    kyc_document2 = models.FileField(upload_to='kyc_docs/', blank=True, null=True)
    # New fields added
    email_id = models.EmailField(max_length=254, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_requests')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_requests')
    resolution = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    #comments = models.TextField(blank=True, null=True)  REMOVED THIS - USING COMMENT MODEL

    def __str__(self):
        return f"{self.tracking_id} - {self.registration_number}"

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)


class ActivityLog(models.Model):
    request = models.ForeignKey(QuotationRequest, on_delete=models.CASCADE, related_name='activity_logs')
    status = models.CharField(max_length=20, choices=QuotationRequest.STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.request.tracking_id} - {self.status} - {self.timestamp}"

class Comment(models.Model):
    quotation_request = models.ForeignKey(QuotationRequest, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}"

class QuoteAttachment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Changes Requested', 'Changes Requested'),
    ]

    request = models.ForeignKey(QuotationRequest, on_delete=models.CASCADE, related_name='quote_attachments')
    file = models.FileField(upload_to='quote_attachments/', blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Quote for {self.request.tracking_id} - {self.file.name} ({self.status})"


class QuoteChangeRequest(models.Model):
    quote = models.ForeignKey(QuoteAttachment, on_delete=models.CASCADE, related_name='change_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    ], default='Pending')
    resolution_comments = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='+')
    resolution_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Change Request for Quote {self.quote.id} by {self.requested_by.username}"

    class Meta:
        ordering = ['-request_date']


class InspectionRequest(models.Model):
    quotation_request = models.ForeignKey(QuotationRequest, on_delete=models.CASCADE,
                                          related_name='inspection_requests')
    rc_upload = models.FileField(upload_to='inspection_docs/')
    contact_number = models.CharField(max_length=20)
    address = models.TextField()
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inspection Request for {self.quotation_request.tracking_id}"