from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import QuotationRequest, AddOn, Insurer, InspectionRequest
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import User, Group
import re
from datetime import datetime, date

class QuotationRequestForm(forms.ModelForm):
    # Multiple selection fields
    add_ons = forms.ModelMultipleChoiceField(
        queryset=AddOn.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label="Select Add-ons"
    )

    preferred_insurer = forms.ModelMultipleChoiceField(
        queryset=Insurer.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label="Preferred Insurers"
    )

    # RTO Code field with regex validation
    rto_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'DL01',
            'pattern': '[a-zA-Z]{2}\d{2}',
            'title': 'Format: 2 letters + 2 digits (e.g., DL01 or dl01)'
        }),
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z]{2}\d{2}$',
                message='Enter valid RTO code (e.g., UP14, DL01)',
                flags=re.IGNORECASE
            )
        ]
    )
    
    CLAIM_STATUS_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]
    
    claim_status = forms.ChoiceField(
        choices=CLAIM_STATUS_CHOICES,
        required=False,
        widget=forms.RadioSelect,
        label="Claim Status (Last Year)"
    )
    
    # New fields
    email_id = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@domain.com'
        }),
        label="Email ID"
    )
    
    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 12345 67890',
            'pattern': r'^\+?\d{10,15}$',
            'title': 'Enter a valid phone number (10-15 digits, optional country code)'
        }),
        validators=[
            RegexValidator(
                regex=r'^\+?\d{10,15}$',
                message='Enter a valid phone number (10-15 digits, optional country code, e.g., +911234567890 or 1234567890)'
            )
        ],
        label="Phone Number"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_conditional_fields()
        # Set date widget attributes dynamically
        today = date.today().isoformat()
        self.fields['previous_expiry_date'].widget.attrs.update({
            'min': '2000-01-01',
            'max': today
        })
        self.fields['registration_date'].widget.attrs.update({
            'min': '1900-01-01',
            'max': today
        })

    def set_conditional_fields(self):
        business_type = self.data.get('business_type') or self.instance.business_type

        if business_type == 'New Business':
            self.fields['rto_code'].required = True
            self.fields['registration_date'].required = False
            self.fields['registration_number'].required = False
            self.fields['ncb'].required = False
            self.fields['previous_expiry_date'].required = False
            self.fields['claim_status'].required = False
        elif business_type == 'Used':
            self.fields['registration_number'].required = True
            self.fields['registration_date'].required = True
            self.fields['ncb'].required = False
            self.fields['claim_status'].required = False
            self.fields['previous_expiry_date'].required = False
        else:  # Renewal/Rollover
            self.fields['registration_number'].required = True
            self.fields['registration_number'].validators = [
                RegexValidator(
                    regex=r'^[a-zA-Z]{2}\d{2}[a-zA-Z]{2,3}\d{4}$',
                    message='Invalid format. Examples: DL01AB1234, dl01abc1234'
                )
            ]
            if business_type == 'Rollover':
                self.fields['previous_expiry_date'].required = True

    class Meta:
        model = QuotationRequest
        fields = [
            'business_type',
            'registration_number',
            'product_type',
            'coverage_type',
            'make_model_variant',
            'registration_date',
            'rto_code',
            'ncb',
            'previous_expiry_date',
            'claim_status',
            'add_ons',
            'preferred_insurer',
            'preferred_idv',
            'additional_requirements',
            'document1',
            'document2',
            'document3',
            'document4',
            'document5',
            'email_id',
            'phone_number',
            'kyc_document1',
            'kyc_document2',
        ]

        widgets = {
            'business_type': forms.Select(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'DL01AB1234'
            }),
            'product_type': forms.Select(attrs={'class': 'form-control'}),
            'coverage_type': forms.Select(attrs={'class': 'form-control'}),
            'make_model_variant': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maruti Suzuki Swift VXI'
            }),
            'registration_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'ncb': forms.Select(attrs={'class': 'form-control'}),
            'previous_expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'preferred_idv': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '₹ 5,00,000'
            }),
            'additional_requirements': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Any special requirements...'
            }),
            'document1': forms.FileInput(attrs={'class': 'form-control-file'}),
            'document2': forms.FileInput(attrs={'class': 'form-control-file'}),
            'document3': forms.FileInput(attrs={'class': 'form-control-file'}),
            'document4': forms.FileInput(attrs={'class': 'form-control-file'}),
            'document5': forms.FileInput(attrs={'class': 'form-control-file'}),
            'kyc_document1': forms.FileInput(attrs={'class': 'form-control-file'}),
            'kyc_document2': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

        labels = {
            'ncb': "No Claim Bonus (NCB)",
            'previous_expiry_date': "Previous Policy Expiry Date",
            'preferred_idv': "Preferred Insured Declared Value (IDV)",
            'kyc_document1': "KYC Document 1",
            'kyc_document2': "KYC Document 2",
        }

        help_texts = {
            'ncb': "Select applicable No Claim Bonus percentage",
            'previous_expiry_date': "Last policy expiry date if renewal",
            'preferred_idv': "Leave blank for insurer calculation",
            'kyc_document1': "Upload first KYC document (e.g., Aadhaar, PAN)",
            'kyc_document2': "Upload second KYC document (e.g., Voter ID, Passport)",
        }

    def clean(self):
        cleaned_data = super().clean()
        business_type = cleaned_data.get('business_type')
        today = date.today()

        # New Business Validation
        if business_type == 'New Business':
            rto_code = cleaned_data.get('rto_code')
            if not rto_code:
                self.add_error('rto_code', "RTO Code is required for new business")
            elif not re.match(r'^[a-zA-Z]{2}\d{2}$', rto_code, re.IGNORECASE):
                self.add_error('rto_code', "Invalid RTO format. Example: DL01")
        
        # Existing/Break-In Business Validation
        else:
            reg_num = cleaned_data.get('registration_number')
            if not reg_num:
                self.add_error('registration_number', "Registration number required")
            elif not re.match(r'^[a-zA-Z]{2}\d{2}[a-zA-Z]{2,3}\d{4}$', reg_num):
                self.add_error('registration_number',
                             "Invalid format. Examples: DL01AB1234, dl01abc1234")

            # Validate NCB and Claim Status
            claim_status = cleaned_data.get('claim_status')
            ncb = cleaned_data.get('ncb')
            if claim_status == 'Yes' and ncb not in ['0%', None]:
                self.add_error('ncb',
                             "NCB cannot be applied if claims were made last year")

        # Date Validation
        reg_date = cleaned_data.get('registration_date')
        prev_expiry = cleaned_data.get('previous_expiry_date')
        if reg_date and prev_expiry and prev_expiry <= reg_date:
            self.add_error('previous_expiry_date',
                         "Previous policy expiry must be after registration date")
        
        # Rollover-specific Validation
        if business_type == 'Rollover' and prev_expiry:
            if prev_expiry < today:
                self.add_error('previous_expiry_date',
                             "For Rollover, expiry date must be today or later")

        # File Upload Validation
        allowed_types = ["application/pdf", "image/jpeg", "image/jpg", "image/png"]
        for field_name in ["document1", "document2", "document3", "document4", "document5", "kyc_document1", "kyc_document2"]:
            file = cleaned_data.get(field_name)
            if file and isinstance(file, UploadedFile):
                if file.content_type not in allowed_types:
                    self.add_error(field_name, "Only PDF, JPEG, JPG, and PNG files are allowed.")

        return cleaned_data

class InspectionRequestForm(forms.ModelForm):
    class Meta:
        model = InspectionRequest
        fields = ['rc_upload', 'contact_number', 'address']
        widgets = {
            'rc_upload': forms.FileInput(attrs={'class': 'form-control-file'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter contact number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter full address'})
        }

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if not re.match(r'^\+?\d{10,15}$', contact_number):
            raise ValidationError("Enter a valid contact number (10-15 digits, optional country code, e.g., +911234567890 or 1234567890)")
        return contact_number

    def clean_rc_upload(self):
        rc_upload = self.cleaned_data.get('rc_upload')
        if rc_upload:
            allowed_types = ["application/pdf", "image/jpeg", "image/jpg", "image/png"]
            if rc_upload.content_type not in allowed_types:
                raise ValidationError("Only PDF, JPEG, JPG, and PNG files are allowed for RC upload.")
        return rc_upload

class AssignRequestForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Engineers', is_active=True),
        label="Assign to Engineer",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = QuotationRequest
        fields = ['assigned_to']

    def clean_assigned_to(self):
        assigned_to = self.cleaned_data.get('assigned_to')
        if not assigned_to:
            raise ValidationError("Please select an engineer to assign the request to.")
        return assigned_to
