from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.core.paginator import Paginator
from .models import QuotationRequest, Insurer, ActivityLog, QuoteAttachment, QuoteChangeRequest, InspectionRequest, Comment
from .forms import QuotationRequestForm, InspectionRequestForm
from django.contrib.auth.models import User
from django.contrib import messages
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Configure logging
logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_staff

def log_activity(request, quotation_request, status, description):
    try:
        ActivityLog.objects.create(
            request=quotation_request,
            status=status,
            user=request.user,
            description=description
        )
        logger.info(f"Activity logged: {description} for request {quotation_request.tracking_id}")
    except Exception as e:
        logger.error(f"Error logging activity: {e}", exc_info=True, stack_info=True)

def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        elif request.user.groups.filter(name='Engineers').exists():
            return redirect('engineer_dashboard')
        else:
            return redirect('agent_dashboard')
    return render(request, 'tickets/home.html')

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            elif user.groups.filter(name='Engineers').exists():
                return redirect('engineer_dashboard')
            else:
                return redirect('agent_dashboard')
        else:
            messages.error(request, 'Invalid credentials.')
    return render(request, 'tickets/login.html')

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('custom_login')

@login_required
def raise_quotation_request(request):
    if request.method == 'POST':
        form = QuotationRequestForm(request.POST, request.FILES)
        if form.is_valid():
            quotation_request = form.save(commit=False)
            quotation_request.created_by = request.user
            quotation_request.save()
            form.save_m2m()
            log_activity(request, quotation_request, 'Open',
                        f'Raised ticket with email {quotation_request.email_id} and phone {quotation_request.phone_number}')
            messages.success(request, "Quotation request raised successfully.")
            return redirect('agent_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
            logger.warning(f"Form errors in raise_quotation_request: {form.errors}")
    else:
        form = QuotationRequestForm()
    return render(request, 'tickets/raise_quotation_request.html', {'form': form})

@login_required
def agent_dashboard(request):
    if request.user.is_staff or request.user.groups.filter(name='Engineers').exists():
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('custom_login')
    registration_number_filter = request.GET.get('registration_number', None)
    product_type_filter = request.GET.get('product_type', None)
    coverage_type_filter = request.GET.get('coverage_type', None)
    business_type_filter = request.GET.get('business_type', None)
    status_filter = request.GET.get('status', None)
    page_number = request.GET.get('page', 1)

    quotation_requests = QuotationRequest.objects.filter(created_by=request.user).order_by('-created_at')

    if registration_number_filter:
        quotation_requests = quotation_requests.filter(registration_number__icontains=registration_number_filter)
    if product_type_filter:
        quotation_requests = quotation_requests.filter(product_type=product_type_filter)
    if coverage_type_filter:
        quotation_requests = quotation_requests.filter(coverage_type=coverage_type_filter)
    if business_type_filter:
        quotation_requests = quotation_requests.filter(business_type=business_type_filter)
    if status_filter:
        quotation_requests = quotation_requests.filter(status=status_filter)

    paginator = Paginator(quotation_requests, 10)
    page_obj = paginator.get_page(page_number)

    form = QuotationRequestForm()
    product_type_choices = form.fields['product_type'].choices
    coverage_type_choices = form.fields['coverage_type'].choices
    business_type_choices = form.fields['business_type'].choices

    return render(request, 'tickets/agent_dashboard.html', {
        'page_obj': page_obj,
        'registration_number_filter': registration_number_filter,
        'product_type_filter': product_type_filter,
        'coverage_type_filter': coverage_type_filter,
        'business_type_filter': business_type_filter,
        'status_filter': status_filter,
        'product_type_choices': product_type_choices,
        'coverage_type_choices': coverage_type_choices,
        'business_type_choices': business_type_choices,
    })

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    status_filter = request.GET.get('status', None)
    search_query = request.GET.get('q', None)
    page_number = request.GET.get('page', 1)
    quotation_requests = QuotationRequest.objects.all().order_by('-created_at')
    if status_filter:
        quotation_requests = quotation_requests.filter(status=status_filter)
    if search_query:
        quotation_requests = quotation_requests.filter(
            Q(tracking_id__icontains=search_query) |
            Q(registration_number__icontains=search_query)
        )
    paginator = Paginator(quotation_requests, 10)
    page_obj = paginator.get_page(page_number)
    return render(request, 'tickets/admin_dashboard.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    })

@login_required
@user_passes_test(is_admin)
def assign_request(request, request_id):
    quotation_request = get_object_or_404(QuotationRequest, id=request_id)
    if request.method == 'POST':
        engineer_id = request.POST.get('engineer')
        if engineer_id:
            engineer = User.objects.get(id=engineer_id)
            quotation_request.assigned_to = engineer
            quotation_request.status = 'Assigned'
            quotation_request.save()
            log_activity(request, quotation_request, 'Assigned', f'Assigned to {engineer.username}')
            return redirect('admin_dashboard')
    engineers = User.objects.filter(is_staff=True)
    return render(request, 'tickets/assign_request.html', {
        'quotation_request': quotation_request,
        'engineers': engineers,
    })

@login_required
def engineer_dashboard(request):
    if not request.user.groups.filter(name='Engineers').exists():
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('custom_login')
    quotation_requests = QuotationRequest.objects.filter(assigned_to=request.user).order_by('-created_at')
    page_number = request.GET.get('page', 1)
    paginator = Paginator(quotation_requests, 10)
    page_obj = paginator.get_page(page_number)
    return render(request, 'tickets/engineer_dashboard.html', {
        'page_obj': page_obj,
    })

@login_required
def resolve_request(request, request_id):
    quotation_request = get_object_or_404(QuotationRequest, id=request_id, assigned_to=request.user)
    insurer_labels = {
        0: "Insurer A",
        1: "Insurer B",
        2: "Insurer C",
        3: "Insurer D",
        4: "Insurer E",
        5: "Insurer F",
    }
    quotes_with_labels = [
        (quote, insurer_labels.get(i, "Unknown Insurer"))
        for i, quote in enumerate(quotation_request.quote_attachments.order_by('uploaded_at'))
    ]
    if request.method == 'POST':
        try:
            if 'send_payment_link' in request.POST:
                if quotation_request.status == 'Payment':
                    quotation_request.status = 'Payment Link Shared'
                    quotation_request.save()
                    log_activity(request, quotation_request, 'Payment Link Shared', f'Payment link shared by {request.user.username}')
                    messages.success(request, "Payment link status updated successfully.")
                    return redirect('engineer_dashboard')
                else:
                    messages.error(request, "Cannot send payment link unless the request is in 'Payment' state.")
                    return redirect('resolve_request', request_id=request_id)
            else:
                for i in range(1, 6):
                    file_key = f'quote_{i}'
                    if file_key in request.FILES:
                        quote_file = request.FILES[file_key]
                        QuoteAttachment.objects.create(
                            request=quotation_request,
                            file=quote_file,
                            uploaded_by=request.user
                        )
                quotation_request.status = 'Resolved'
                quotation_request.save()
                log_activity(request, quotation_request, 'Resolved', 'Quotes uploaded and request resolved')
                messages.success(request, "Quotes uploaded and request resolved successfully.")
                return redirect('engineer_dashboard')
        except Exception as e:
            logger.exception(f"Error resolving request {request_id}: {e}", exc_info=True)
            messages.error(request, f"An error occurred: {e}")
    return render(request, 'tickets/resolve_request.html', {
        'quotation_request': quotation_request,
        'quotes_with_labels': quotes_with_labels,
    })

@login_required
@user_passes_test(is_admin)
def mark_incomplete(request, request_id):
    quotation_request = get_object_or_404(QuotationRequest, id=request_id)
    if request.method == 'POST':
        comment = request.POST.get('comment')
        if comment:
            quotation_request.comments = comment
        quotation_request.status = 'Incomplete'
        quotation_request.save()
        log_activity(request, quotation_request, 'Incomplete', 'Marked as incomplete')
        return redirect('assign_request', request_id=request_id)
    return redirect('assign_request', request_id=request_id)

@login_required
def edit_request(request, request_id):
    quotation_request = get_object_or_404(QuotationRequest, id=request_id)
    if request.method == 'POST':
        form = QuotationRequestForm(request.POST, request.FILES, instance=quotation_request)
        if form.is_valid():
            old_status = quotation_request.status
            quotation_request = form.save(commit=False)
            if old_status == 'Incomplete':
                quotation_request.status = 'Open'
                log_activity(request, quotation_request, 'Open', 'Resubmitted after incomplete')
            quotation_request.save()
            form.save_m2m()
            return redirect('agent_dashboard')
        else:
            print("Form errors:", form.errors)
    else:
        form = QuotationRequestForm(instance=quotation_request)
    return render(request, 'tickets/edit_request.html', {'form': form, 'quotation_request': quotation_request})

@login_required
def view_request(request, request_id):
    quotation_request = get_object_or_404(QuotationRequest, id=request_id)
    if quotation_request.created_by != request.user:
        return redirect('agent_dashboard')
    insurer_labels = {
        0: "Insurer A",
        1: "Insurer B",
        2: "Insurer C",
        3: "Insurer D",
        4: "Insurer E",
        5: "Insurer F",
    }
    quotes_with_labels = [
        (quote, insurer_labels.get(i, "Unknown Insurer"))
        for i, quote in enumerate(quotation_request.quote_attachments.order_by('uploaded_at'))
    ]
    change_requests = QuoteChangeRequest.objects.filter(quote__in=quotation_request.quote_attachments.all())
    inspection_form = InspectionRequestForm()
    return render(request, 'tickets/view_request.html', {
        'quotation_request': quotation_request,
        'quotes_with_labels': quotes_with_labels,
        'change_requests': change_requests,
        'inspection_form': inspection_form,
    })

@login_required
def accept_quote(request, request_id, quote_id):
    quotation_request = get_object_or_404(QuotationRequest, id=request_id)
    quote = get_object_or_404(QuoteAttachment, id=quote_id, request=quotation_request)
    if request.method == 'POST' and quotation_request.created_by == request.user:
        if quotation_request.quote_attachments.filter(status='Accepted').exists():
            messages.error(request, "A quote has already been accepted. No further actions are allowed.")
            return redirect('view_request', request_id=request_id)
        if quote.status == 'Pending':
            quote.status = 'Accepted'
            quote.save()
            quotation_request.status = 'Accepted'
            quotation_request.save()
            log_activity(request, quotation_request, 'Accepted', f'Quote {quote.file.name} accepted')
            messages.success(request, "Quote accepted successfully.")
        else:
            messages.error(request, "Only pending quotes can be accepted.")
    return redirect('view_request', request_id=request_id)

@login_required
def reject_quote(request, request_id, quote_id):
    quotation_request = get_object_or_404(QuotationRequest, id=request_id)
    quote = get_object_or_404(QuoteAttachment, id=quote_id, request=quotation_request)
    if request.method == 'POST' and quotation_request.created_by == request.user:
        if quotation_request.quote_attachments.filter(status='Accepted').exists():
            messages.error(request, "A quote has already been accepted. No further actions are allowed.")
            return redirect('view_request', request_id=request_id)
        if quote.status == 'Pending':
            quote.status = 'Rejected'
            quote.save()
            log_activity(request, quotation_request, 'Rejected', f'Quote {quote.file.name} rejected')
            messages.success(request, "Quote rejected successfully.")
        else:
            messages.error(request, "Only pending quotes can be rejected.")
    return redirect('view_request', request_id=request_id)

@login_required
def request_payment_link(request, request_id):
    quotation_request = get_object_or_404(QuotationRequest, id=request_id)
    if quotation_request.created_by != request.user or quotation_request.status != 'Accepted':
        return redirect('view_request', request_id=request_id)
    if request.method == 'POST':
        kyc1 = request.FILES.get('kyc_document1')
        kyc2 = request.FILES.get('kyc_document2')
        if kyc1 or kyc2:
            if kyc1:
                quotation_request.kyc_document1 = kyc1
            if kyc2:
                quotation_request.kyc_document2 = kyc2
            quotation_request.status = 'Payment'
            quotation_request.save()
            log_activity(request, quotation_request, 'Payment Requested', 'KYC documents uploaded for payment link')
            messages.success(request, "Payment link requested successfully.")
            return redirect('view_request', request_id=request_id)
    return redirect('view_request', request_id=request_id)

@login_required
@require_POST
def request_quote_change_ajax(request):
    quote_id = request.POST.get('quote_id')
    reason = request.POST.get('reason')
    quotation_request_id = request.POST.get('quotation_request_id')
    try:
        quotation_request = get_object_or_404(QuotationRequest, pk=quotation_request_id, created_by=request.user)
        quote = get_object_or_404(QuoteAttachment, pk=quote_id, request=quotation_request)
        if quotation_request.quote_attachments.filter(status='Accepted').exists():
            return JsonResponse({'status': 'error', 'message': 'A quote has already been accepted. No further changes are allowed.'})
        if not reason:
            return JsonResponse({'status': 'error', 'message': 'Please provide a reason for the change request.'})
        change_request = QuoteChangeRequest(
            quote=quote,
            requested_by=request.user,
            reason=reason
        )
        change_request.save()
        quotation_request.status = 'Changes Requested'
        quotation_request.save()
        log_activity(request, quotation_request, 'Changes Requested', f'Change requested for quote {quote.file.name}')
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.exception("Error processing quote change request:", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def request_quote_change(request, quotation_request_id, quote_id):
    quotation_request = get_object_or_404(QuotationRequest, pk=quotation_request_id)
    quote = get_object_or_404(QuoteAttachment, pk=quote_id)
    if request.method == 'POST' and quotation_request.created_by == request.user:
        if quotation_request.quote_attachments.filter(status='Accepted').exists():
            messages.error(request, "A quote has already been accepted. No further changes are allowed.")
            return redirect('view_request', quotation_request_id)
        reason = request.POST.get('reason')
        if reason:
            change_request = QuoteChangeRequest(
                quote=quote,
                requested_by=request.user,
                reason=reason
            )
            change_request.save()
            quotation_request.status = 'Changes Requested'
            quotation_request.save()
            log_activity(request, quotation_request, 'Changes Requested',
                        f'Change requested for quote {quote.file.name}')
            messages.success(request, "Change request submitted successfully.")
            return redirect('view_request', quotation_request_id)
        else:
            messages.error(request, "Please provide a reason for the change request.")
    else:
        messages.error(request, "Invalid request method.")
    return redirect('view_request', quotation_request_id)

@login_required
def request_inspection(request, request_id):
    quotation_request = get_object_or_404(QuotationRequest, id=request_id, created_by=request.user)
    if quotation_request.business_type not in ['Break-In', 'Used']:
        messages.error(request, "Inspection is not required for this business type.")
        return redirect('view_request', request_id=request_id)
    if request.method == 'POST':
        form = InspectionRequestForm(request.POST, request.FILES)
        if form.is_valid():
            inspection = form.save(commit=False)
            inspection.quotation_request = quotation_request
            inspection.save()
            quotation_request.status = 'Inspection Requested'
            quotation_request.save()
            log_activity(request, quotation_request, 'Inspection Requested', 'Inspection requested by agent')
            messages.success(request, "Inspection requested successfully.")
            return redirect('view_request', request_id=request_id)
        else:
            messages.error(request, "Please correct the errors in the inspection form.")
    else:
        messages.error(request, "Invalid request method.")
    return redirect('view_request', request_id=request_id)

@login_required
def add_comment(request, quotation_request_id):
    quotation_request = get_object_or_404(QuotationRequest, pk=quotation_request_id)
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text')
        return_url = request.POST.get('return_url', 'view_request')
        if comment_text:
            Comment.objects.create(quotation_request=quotation_request, user=request.user, text=comment_text)
        if return_url == 'resolve_request':
            return redirect('resolve_request', request_id=quotation_request_id)
        return redirect('view_request', request_id=quotation_request_id)
    return redirect('view_request', request_id=quotation_request_id)