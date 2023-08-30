import threading
import time
from datetime import datetime, timedelta

import geopy.distance
import pytz
from authentication.forms import UserDetailCompleteForm
from authentication.models import Profile
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView
from google.cloud.firestore_v1 import FieldFilter


from .forms import CameraForm
from .models import CameraModel

db = settings.FIRESTORE_DB
camera_db = db.collection("Cameras")
detected_db = db.collection("Detected")
user_db = db.collection("Users")
storage = settings.FIREBASE_BUCKET
camera_names, detected_time_list, offline_user_ids, detection_ids = [], [], [], []
# Create an Event for notifying main thread.
delete_done = threading.Event()


def on_snapshot(col_snapshot, changes, read_time):
    for change in changes:
        dict_doc = change.document.to_dict()
        if dict_doc["accuracy"] == 0 and dict_doc["detected_time"] not in detected_time_list:
            if change.type.name == "ADDED":
                detected_time_list.append(dict_doc["detected_time"])
                detection_ids.append(change.document.id)
                camera_names.append(dict_doc["camera_name"])
                offline_user_ids.append(dict_doc["offline_user_id"])
            elif change.type.name == "MODIFIED":
                if dict_doc["accuracy"] != 0:
                    detected_time_list.remove(dict_doc["detected_time"])
                    camera_names.remove(dict_doc["camera_name"])
                    detection_ids.remove(change.document.id)
                    offline_user_ids.remove(dict_doc["offline_user_id"])
            elif change.type.name == "REMOVED":
                detected_time_list.remove(dict_doc["detected_time"])
                camera_names.remove(dict_doc["camera_name"])
                detection_ids.remove(change.document.id)
                offline_user_ids.remove(dict_doc["offline_user_id"])
                delete_done.set()


class AdminDashboardView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'director/index.html'

    def get_context_data(self, **kwargs):
        context = super(AdminDashboardView, self).get_context_data(**kwargs)
        try:

            user = self.request.user
            col_query = db.collection("Detected").where(filter=FieldFilter("offline_user_id", "==", user.id))
            query_watch = col_query.on_snapshot(on_snapshot)
            context['length_notification'] = len(camera_names)
            context['detection'] = zip(detected_time_list, camera_names, detection_ids)
            context['last_week'] = timezone.now().date() - timedelta(days=7)
            context['last_30'] = timezone.now().date() - timedelta(days=30)
            context['date'] = datetime.today().date()
            context["cameras"] = CameraModel.objects.filter(user_id=user.id)
            context["profile"] = user.profile
            det_docs = db.collection("Detected").where(filter=FieldFilter("offline_user_id", "==", user.id)).stream()
            t_d = 0
            t_a = 0
            context['x_week_label'] = [(str(timezone.now().date() - timedelta(days=i))) for i in range(7)]
            context['y_week_label'] = []
            context['y_week_acc'] = []
            context['x_month_label'] = [(str(timezone.now().date() - timedelta(days=i))) for i in range(30)]
            context['y_month_label'] = []
            context['y_month_acc'] = []

            acc_str_list = []
            for doc in det_docs:
                if doc.to_dict()["accuracy"] != 0:
                    if doc.to_dict()["accuracy"] == 1:
                        t_a += 1
                    acc_str_list.append(
                        str(doc.to_dict()["detected_time"]).split(" ")[0] + "#" + str(doc.to_dict()["accuracy"]))
                    t_d += 1
            t_w_d = 0
            t_w_a = 0
            for w_date in context['x_week_label']:
                y_d = 0
                x_d = 0
                for acc_str in acc_str_list:
                    if w_date == acc_str.split("#")[0]:
                        if acc_str.split("#")[1] == "1":
                            y_d += 1
                        x_d += 1
                context['y_week_acc'].append(round(y_d*100/x_d, 2) if x_d >0 else 0)
                context['y_week_label'].append(x_d)
            for m_date in context['x_month_label']:
                y_d = 0
                x_d = 0
                for acc_str in acc_str_list:
                    if m_date == acc_str.split("#")[0]:
                        if acc_str.split("#")[1] == "1":
                            y_d += 1
                        x_d += 1
                t_w_a += y_d
                t_w_d += x_d
                context['y_month_acc'].append(round(y_d*100/x_d, 2) if x_d >0 else 0)
                context['y_month_label'].append(x_d)
            print(t_w_d)
            print(t_w_a)
            context['total_weekly_detection'] = t_w_d
            context['total_weekly_accuracy'] = t_w_a
            context['total_weekly_percent'] = round(t_w_a*100/t_w_d, 2)
            context['total_detection'] = t_d
            context['total_true_positive'] = t_a
            context['total_accuracy'] = round(t_a * 100 / t_d, 2)

        except ObjectDoesNotExist:
            context["fill_the_requirements"] = True
        return context


class AdminCameraListView(LoginRequiredMixin, ListView):
    template_name = 'director/camera_list.html'
    model = User

    def get_context_data(self, **kwargs):
        context = super(AdminCameraListView, self).get_context_data(**kwargs)
        user = self.request.user
        try:
            col_query = db.collection("Detected").where(filter=FieldFilter("offline_user_id", "==", user.id))
            context['length_notification'] = len(camera_names)
            context['detection'] = zip(detected_time_list, camera_names, detection_ids)
            query_watch = col_query.on_snapshot(on_snapshot)

            context['distances'] = []
            context['total_det'] = []
            context['acc_score'] = []
            context['date'] = datetime.today().date()
            context["cameras"] = CameraModel.objects.filter(user_id=user.id)
            context["profile"] = user.profile
            lat1 = float(context["profile"].location.split(",")[0])
            lon1 = float(context["profile"].location.split(",")[1])
            for camera in context["cameras"]:
                det_docs = db.collection("Detected").where(
                    filter=FieldFilter("camera_name", "==", camera.camera_name)).stream()
                t_d = 0
                t_a = 0
                for doc in det_docs:
                    if doc.to_dict()["accuracy"] != 0:
                        if doc.to_dict()["accuracy"] == 1:
                            t_a += 1
                        t_d += 1

                context['total_det'].append(f"{t_a}/{t_d}")
                context['acc_score'].append(round(t_a * 100 / t_d, 2) if t_d > 0 else "failed")
                lat2 = float(camera.location.split(",")[0])
                lon2 = float(camera.location.split(",")[1])
                cords_1 = (lat1, lon1)
                cords_2 = (lat2, lon2)
                context['distances'].append(str(round(geopy.distance.geodesic(cords_1, cords_2).km, 2)) + " km")

            context["zipped_data"] = zip(context["distances"], context["cameras"], context['total_det'],
                                         context['acc_score'])
        except ObjectDoesNotExist:
            context["fill_the_requirements"] = True
        return context


class AdminDetectionListView(LoginRequiredMixin, ListView):
    template_name = 'director/detection_list.html'
    model = User

    def get_context_data(self, **kwargs):
        context = super(AdminDetectionListView, self).get_context_data(**kwargs)
        user = self.request.user
        try:
            col_query = detected_db.where(filter=FieldFilter("offline_user_id", "==", user.id))
            query_watch = col_query.on_snapshot(on_snapshot)
            context['length_notification'] = len(camera_names)
            context['detection'] = zip(detected_time_list, camera_names, detection_ids)
            context["profile"] = user.profile
            det_list = detected_db.where(filter=FieldFilter("offline_user_id", "==", user.id)).stream()
            det_id, acc, cam_name, cap_img, det_img, det_time = [], [], [], [], [], []
            for doc in det_list:
                dict_doc = doc.to_dict()
                det_id.append(doc.id)
                acc.append(dict_doc["accuracy"])
                cam_name.append(dict_doc["camera_name"])
                cap_img.append(dict_doc["captured_image_url"])
                det_img.append(dict_doc["detected_image_url"])
                det_time.append(dict_doc["detected_time"])
                context['detection_list'] = zip(det_id, acc, cam_name, cap_img, det_img, det_time)
        except ObjectDoesNotExist:
            context["fill_the_requirements"] = True
        return context


@login_required
def AdminAddCameraView(request):
    try:
        user = request.user
        col_query = db.collection("Detected").where(filter=FieldFilter("offline_user_id", "==", user.id))
        query_watch = col_query.on_snapshot(on_snapshot)

        registered = False
        if request.method == "POST":
            user_doc = user_db.document(request.user.first_name)
            form = CameraForm(data=request.POST)
            if form.is_valid():
                c_form = form.save(commit=False)
                data = {
                    'camera_name': form.cleaned_data['camera_name'],
                    'city': form.cleaned_data['city'],
                    'location': form.cleaned_data['location'],
                    'web_address': form.cleaned_data['web_address'],
                    'added_date': datetime.now(pytz.timezone('Asia/Tashkent')),
                    'user_offline_id': request.user.id,
                    'user_online_id': user_doc.id,
                }
                camera_db.add(data)
                c_form.user_id = request.user
                c_form.save()
                registered = True
        else:
            form = CameraForm()
        context = {'form': form, "registered": registered,
                   "profile": request.user.profile,
                   "length_notification": len(camera_names),
                   "detection": zip(detected_time_list, camera_names, detection_ids)
                   }
    except ObjectDoesNotExist:
        context = {'fill_the_requirements': True}
    return render(request, "director/add_camera.html", context)


@login_required
def AdminUpdateProfileView(request):
    try:
        user = request.user
        col_query = db.collection("Detected").where(filter=FieldFilter("offline_user_id", "==", user.id))
        query_watch = col_query.on_snapshot(on_snapshot)
        registered = False
        profile_data = get_object_or_404(Profile, id=request.user.profile.id)
        profile_form = UserDetailCompleteForm(instance=profile_data)
        if request.method == "POST":
            print(request.user.first_name)
            profile_form = UserDetailCompleteForm(request.POST, instance=profile_data)
            if profile_form.is_valid():
                c_form = profile_form.save(commit=False)
                data = {
                    'company': profile_form.cleaned_data['company'],
                    'city': profile_form.cleaned_data['city'],
                    'location': profile_form.cleaned_data['location'],
                    'phone': profile_form.cleaned_data['phone']
                }
                print(request.user.first_name)
                user_doc = user_db.document(request.user.first_name)
                user_doc.update(data)
                c_form.save()
                registered = True
            else:
                profile_form = UserDetailCompleteForm()
        context = {'form': profile_form, "registered": registered, "profile": request.user.profile,
                   "length_notification": len(camera_names),
                   "detection": zip(detected_time_list, camera_names, detection_ids)
                   }
    except ObjectDoesNotExist:
        context = {'fill_the_requirements': True}
    return render(request, "director/profile_update.html", context)


@login_required
def AdminProfileSettingView(request):
    registered = False
    if request.method == "POST":
        form = UserDetailCompleteForm(data=request.POST)
        if form.is_valid():
            c_form = form.save(commit=False)
            data = {
                'company': form.cleaned_data['company'],
                'city': form.cleaned_data['city'],
                'location': form.cleaned_data['location'],
                'phone': form.cleaned_data['phone']
            }
            user_doc = user_db.document(request.user.first_name)
            user_doc.update(data)
            c_form.user_id = request.user.id
            c_form.save()
            registered = True
    else:
        form = UserDetailCompleteForm()
    context = {'form': form, "registered": registered}
    return render(request, "director/profile_setting.html", context)


@login_required
def cameraDetailView(request, pk):
    user = request.user
    col_query = db.collection("Detected").where(filter=FieldFilter("offline_user_id", "==", user.id))
    query_watch = col_query.on_snapshot(on_snapshot)
    key = settings.GOOGLE_API_KEY
    user = request.user.profile
    camera = get_object_or_404(CameraModel, pk=pk)
    lat1 = float(camera.location.split(",")[0])
    lon1 = float(camera.location.split(",")[1])

    user_lat1 = float(user.location.split(",")[0])
    user_lon1 = float(user.location.split(",")[1])
    form = CameraForm(request.POST or None, instance=camera)
    if request.user.is_active:
        if request.method == 'POST':
            if 'camera_update_btn' in request.POST:
                if form.is_valid():
                    form.save()
            elif 'camera_delete_btn' in request.POST:
                camera.delete()
                return redirect('director:index')
            return redirect('director:cameraDetail', pk=camera.pk)
    context = {
        "latitude1": lat1,
        "longitude1": lon1,

        "user_latitude1": user_lat1,
        "user_longitude1": user_lon1,
        "length_notification": len(camera_names),
        "detection": zip(detected_time_list, camera_names, detection_ids),
        'camera': camera,
        'form': form,
        'key': key,
    }
    return render(request, 'director/camera_detail.html', context)


@login_required
def detectionDetailView(request, det_id):
    user = request.user
    col_query = db.collection("Detected").where(filter=FieldFilter("offline_user_id", "==", user.id))
    query_watch = col_query.on_snapshot(on_snapshot)
    doc_ref = db.collection("Detected").document(det_id).get()
    dict_ref = doc_ref.to_dict()

    key = settings.GOOGLE_API_KEY
    user = request.user.profile
    # camera = get_object_or_404(CameraModel, camera_name=dict_ref["camera_name"])[0]
    camera = CameraModel.objects.get(camera_name=dict_ref["camera_name"])
    detected_time = dict_ref["detected_time"]
    captured_image_url = dict_ref["captured_image_url"]
    detected_image_url = dict_ref["detected_image_url"]
    detected_classes = dict_ref["detected_classes"]
    detected_accuracy = dict_ref["accuracy"]
    lat1 = float(camera.location.split(",")[0])
    lon1 = float(camera.location.split(",")[1])

    user_lat1 = float(user.location.split(",")[0])
    user_lon1 = float(user.location.split(",")[1])
    form = CameraForm(request.POST or None, instance=camera)
    if request.user.is_active:
        if request.method == 'POST':
            if 'true_positive_btn' in request.POST:
                db.collection("Detected").document(det_id).update({"accuracy": 1})
            elif 'false_positive_btn' in request.POST:
                db.collection("Detected").document(det_id).update({"accuracy": -1})
            return redirect('director:detectionList')
    context = {
        "latitude1": lat1,
        "longitude1": lon1,
        'detected_accuracy': detected_accuracy,
        "user_latitude1": user_lat1,
        "user_longitude1": user_lon1,
        "length_notification": len(camera_names),
        "detection": zip(detected_time_list, camera_names, detection_ids),
        'camera': camera,
        'form': form,
        'key': key,
        "detected_time": detected_time,
        "captured_image_url": captured_image_url,
        "detected_image_url": detected_image_url,
        "detected_classes": detected_classes,
    }
    return render(request, 'director/detection_detail.html', context)
