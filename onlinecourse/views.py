from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        try:
            Enrollment.objects.get(user=user, course=course)
            is_enrolled = True
        except:
            is_enrolled = False
    return is_enrolled


def index(request):
    context = {}
    if request.user.is_authenticated:
        courses = Course.objects.filter(total_enrollment__gt=0)
        for course in courses:
            if check_if_enrolled(request.user, course):
                course.is_enrolled = True
        context = {'courses': courses}
    return render(request, 'onlinecourse/course_list_bootstrap.html', context)


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()
    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


def course_details(request, course_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    context['course'] = course
    return render(request, 'onlinecourse/course_details_bootstrap.html', context)


def submit(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.get(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    choices = []
    for key, values in request.POST.items():
        if key.startswith('choice'):
            for value in values:
                selected_ids = int(value)
                choice = Choice.objects.get(pk=selected_ids)
                submission.choices.add(choice)
    submission.save()
    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course_id, submission.id)))


def show_exam_result(request, course_id, submission_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    choices = submission.choices.all()
    total_score = 0
    for question in course.question_set.all():
        selected_ids = choices.filter(question=question).values_list('id', flat=True)
        if question.is_get_score(selected_ids):
            total_score += question.grade
    context['course'] = course
    context['submission'] = submission
    context['choices'] = choices
    context['total_score'] = total_score
    context['passed'] = total_score >= 80
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
