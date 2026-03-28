# government_schemes/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import SchemeInterest


# ── Static list of major Indian government farming schemes ──
STATIC_SCHEMES = [
    {
        'id': 1,
        'name': 'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Direct income support of ₹6,000 per year to all farmer families in three equal installments of ₹2,000 each.',
        'benefit': '₹6,000/year',
        'eligibility': 'All landholding farmer families',
        'category': 'income_support',
        'emoji': '💰',
        'link': 'https://pmkisan.gov.in/',
        'color': 'green',
    },
    {
        'id': 2,
        'name': 'PM Fasal Bima Yojana (PMFBY)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Crop insurance scheme providing financial support to farmers suffering crop loss/damage due to unforeseen events.',
        'benefit': 'Crop loss compensation',
        'eligibility': 'All farmers growing notified crops',
        'category': 'insurance',
        'emoji': '🛡️',
        'link': 'https://pmfby.gov.in/',
        'color': 'blue',
    },
    {
        'id': 3,
        'name': 'Kisan Credit Card (KCC)',
        'ministry': 'Ministry of Finance',
        'description': 'Provides farmers with affordable credit for agricultural needs including crop cultivation, post-harvest expenses and farm maintenance.',
        'benefit': 'Credit up to ₹3 lakh at 7% interest',
        'eligibility': 'Farmers, tenant farmers, sharecroppers',
        'category': 'credit',
        'emoji': '💳',
        'link': 'https://www.nabard.org/content.aspx?id=572',
        'color': 'gold',
    },
    {
        'id': 4,
        'name': 'PM Krishi Sinchai Yojana (PMKSY)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Aims to extend coverage of irrigation to every farm and improve water use efficiency with "More Crop Per Drop" approach.',
        'benefit': 'Subsidy on irrigation equipment',
        'eligibility': 'All farmers, priority to small/marginal',
        'category': 'irrigation',
        'emoji': '💧',
        'link': 'https://pmksy.gov.in/',
        'color': 'blue',
    },
    {
        'id': 5,
        'name': 'Soil Health Card Scheme',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Provides farmers soil health cards with crop-wise recommendations of nutrients and fertilizers for individual farms.',
        'benefit': 'Free soil testing and recommendations',
        'eligibility': 'All farmers',
        'category': 'soil',
        'emoji': '🌱',
        'link': 'https://soilhealth.dac.gov.in/',
        'color': 'green',
    },
    {
        'id': 6,
        'name': 'National Agriculture Market (e-NAM)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Online trading platform for agricultural commodities providing better price discovery and reducing intermediaries.',
        'benefit': 'Direct market access, better prices',
        'eligibility': 'All farmers registered on platform',
        'category': 'market',
        'emoji': '🏪',
        'link': 'https://enam.gov.in/',
        'color': 'orange',
    },
    {
        'id': 7,
        'name': 'Pradhan Mantri Kisan Maandhan Yojana (PM-KMY)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Pension scheme for small and marginal farmers providing ₹3,000/month pension after age 60.',
        'benefit': '₹3,000/month pension after 60',
        'eligibility': 'Small & marginal farmers aged 18-40',
        'category': 'pension',
        'emoji': '👴',
        'link': 'https://maandhan.in/',
        'color': 'gold',
    },
    {
        'id': 8,
        'name': 'Sub-Mission on Agricultural Mechanization (SMAM)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Promotes farm mechanization by providing subsidies on agricultural machinery and equipment.',
        'benefit': '25-50% subsidy on farm equipment',
        'eligibility': 'Individual farmers, FPOs, cooperatives',
        'category': 'mechanization',
        'emoji': '🚜',
        'link': 'https://agrimachinery.nic.in/',
        'color': 'orange',
    },
    {
        'id': 9,
        'name': 'National Food Security Mission (NFSM)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Aims to increase production of rice, wheat, pulses, coarse cereals through area expansion and productivity enhancement.',
        'benefit': 'Free seeds, fertilizers, training',
        'eligibility': 'Farmers in selected districts',
        'category': 'crop',
        'emoji': '🌾',
        'link': 'https://nfsm.gov.in/',
        'color': 'green',
    },
    {
        'id': 10,
        'name': 'Paramparagat Krishi Vikas Yojana (PKVY)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Promotes organic farming through adoption of organic villages by cluster approach and PGS certification.',
        'benefit': '₹50,000/hectare for 3 years',
        'eligibility': 'Farmers willing to adopt organic farming',
        'category': 'organic',
        'emoji': '🌿',
        'link': 'https://pgsindia-ncof.gov.in/',
        'color': 'green',
    },
    {
        'id': 11,
        'name': 'Agriculture Infrastructure Fund (AIF)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Medium-long term debt financing facility for post-harvest management infrastructure and community farming assets.',
        'benefit': 'Loan up to ₹2 crore at 3% interest subsidy',
        'eligibility': 'Farmers, FPOs, SHGs, cooperatives',
        'category': 'infrastructure',
        'emoji': '🏗️',
        'link': 'https://agriinfra.dac.gov.in/',
        'color': 'blue',
    },
    {
        'id': 12,
        'name': 'PM AASHA (Annadata Aay Sanrakshan Abhiyan)',
        'ministry': 'Ministry of Agriculture & Farmers Welfare',
        'description': 'Ensures farmers receive remunerative prices for their produce through MSP-based procurement and price support.',
        'benefit': 'MSP guarantee for oilseeds & pulses',
        'eligibility': 'Farmers growing oilseeds and pulses',
        'category': 'price_support',
        'emoji': '📊',
        'link': 'https://pib.gov.in/newsite/PrintRelease.aspx?relid=183820',
        'color': 'gold',
    },
]

CATEGORIES = [
    ('all', 'All Schemes', '📋'),
    ('income_support', 'Income Support', '💰'),
    ('insurance', 'Insurance', '🛡️'),
    ('credit', 'Credit & Loans', '💳'),
    ('irrigation', 'Irrigation', '💧'),
    ('soil', 'Soil Health', '🌱'),
    ('market', 'Market Access', '🏪'),
    ('pension', 'Pension', '👴'),
    ('mechanization', 'Mechanization', '🚜'),
    ('crop', 'Crop Support', '🌾'),
    ('organic', 'Organic Farming', '🌿'),
    ('infrastructure', 'Infrastructure', '🏗️'),
    ('price_support', 'Price Support', '📊'),
]


def get_scheme_by_id(scheme_id):
    for s in STATIC_SCHEMES:
        if s['id'] == scheme_id:
            return s
    return None


@login_required
def government_schemes_view(request):
    category = request.GET.get('category', 'all')
    search = request.GET.get('q', '').lower()

    schemes = STATIC_SCHEMES.copy()

    if category != 'all':
        schemes = [s for s in schemes if s['category'] == category]
    if search:
        schemes = [s for s in schemes if
                   search in s['name'].lower() or
                   search in s['description'].lower() or
                   search in s['benefit'].lower()]

    # Get user's interest records
    user_interests = {
        i.scheme_id: i
        for i in SchemeInterest.objects.filter(user=request.user)
    }

    # Attach interest info to each scheme
    for s in schemes:
        interest = user_interests.get(s['id'])
        s['interest'] = interest
        s['self_applied'] = interest.self_marked_applied if interest else False
        s['clicked_apply'] = interest.clicked_apply if interest else False

    context = {
        'schemes': schemes,
        'categories': CATEGORIES,
        'selected_category': category,
        'search': search,
        'total': len(schemes),
    }
    return render(request, 'government_schemes/schemes.html', context)


@login_required
@require_POST
def track_apply_click(request):
    """Called via AJAX when user clicks 'Apply / Learn More'"""
    scheme_id = int(request.POST.get('scheme_id', 0))
    scheme = get_scheme_by_id(scheme_id)
    if not scheme:
        return JsonResponse({'ok': False})

    interest, _ = SchemeInterest.objects.get_or_create(
        user=request.user,
        scheme_id=scheme_id,
        defaults={
            'scheme_name': scheme['name'],
            'scheme_category': scheme['category'],
        }
    )
    interest.clicked_apply = True
    if interest.status == 'interested':
        interest.status = 'interested'
    interest.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def mark_self_applied(request):
    """Called via AJAX when user clicks 'I Applied'"""
    scheme_id = int(request.POST.get('scheme_id', 0))
    scheme = get_scheme_by_id(scheme_id)
    if not scheme:
        return JsonResponse({'ok': False})

    interest, _ = SchemeInterest.objects.get_or_create(
        user=request.user,
        scheme_id=scheme_id,
        defaults={
            'scheme_name': scheme['name'],
            'scheme_category': scheme['category'],
        }
    )
    interest.self_marked_applied = True
    interest.clicked_apply = True
    interest.status = 'applied'
    interest.save()
    return JsonResponse({'ok': True, 'status': 'applied'})