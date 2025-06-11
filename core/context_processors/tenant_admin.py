def tenant_admin(request):
    """Add tenant context to admin templates"""
    context = {}
    if hasattr(request, 'tenant'):
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_platform_admin:
                context['site_header'] = 'Platform Administration'
                context['site_title'] = 'Platform Admin'
            else:
                context['site_header'] = f'{request.tenant.name} Administration'
                context['site_title'] = request.tenant.name
    return context