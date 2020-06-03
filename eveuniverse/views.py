from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required


@login_required
@permission_required('eveuniverse.basic_access')
def index(request):
        
    context = {
        'text': 'Hello, World!'
    }
    # EveCategory.objects.update_or_create_esi(eve_id=32)

    return render(request, 'eveuniverse/index.html', context)
