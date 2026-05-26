from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import admin_required
from .models import Team, TechnologyStack
from .forms import TeamForm, TechnologyStackForm

# --- Team Views ---

@login_required
@admin_required
def team_list(request):
    teams = Team.objects.all()
    return render(request, 'teams/team_list.html', {'teams': teams})

@login_required
@admin_required
def team_create(request):
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Team created successfully.")
            return redirect('team_list')
    else:
        form = TeamForm()
    return render(request, 'teams/team_form.html', {'form': form, 'title': 'Create Team'})

@login_required
@admin_required
def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f"Team '{team.name}' updated successfully.")
            return redirect('team_list')
    else:
        form = TeamForm(instance=team)
    return render(request, 'teams/team_form.html', {'form': form, 'title': 'Edit Team', 'team': team})

@login_required
@admin_required
def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        team.delete()
        messages.success(request, f"Team '{team.name}' deleted successfully.")
        return redirect('team_list')
    return render(request, 'teams/team_confirm_delete.html', {'team': team})

# --- Technology Stack Views ---

@login_required
@admin_required
def stack_list(request):
    stacks = TechnologyStack.objects.all()
    return render(request, 'teams/stack_list.html', {'stacks': stacks})

@login_required
@admin_required
def stack_create(request):
    if request.method == 'POST':
        form = TechnologyStackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Technology Stack created successfully.")
            return redirect('stack_list')
    else:
        form = TechnologyStackForm()
    return render(request, 'teams/stack_form.html', {'form': form, 'title': 'Add Technology Stack'})

@login_required
@admin_required
def stack_update(request, pk):
    stack = get_object_or_404(TechnologyStack, pk=pk)
    if request.method == 'POST':
        form = TechnologyStackForm(request.POST, instance=stack)
        if form.is_valid():
            form.save()
            messages.success(request, f"Technology Stack '{stack.name}' updated successfully.")
            return redirect('stack_list')
    else:
        form = TechnologyStackForm(instance=stack)
    return render(request, 'teams/stack_form.html', {'form': form, 'title': 'Edit Technology Stack', 'stack': stack})

@login_required
@admin_required
def stack_delete(request, pk):
    stack = get_object_or_404(TechnologyStack, pk=pk)
    if request.method == 'POST':
        stack.delete()
        messages.success(request, f"Technology Stack '{stack.name}' deleted successfully.")
        return redirect('stack_list')
    return render(request, 'teams/stack_confirm_delete.html', {'stack': stack})
