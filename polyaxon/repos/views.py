# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import logging
import os

from django.conf import settings
from django.http import HttpResponseServerError

from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    get_object_or_404)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.permissions import get_permissible_project
from repos.serializers import RepoSerializer
from repos.tasks import handle_new_files
from repos.models import Repo

logger = logging.getLogger(__name__)


class RepoDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Repo.objects.all()
    serializer_class = RepoSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return get_object_or_404(Repo, project=get_permissible_project(view=self))


class UploadFilesView(APIView):
    parser_classes = (MultiPartParser,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        project = get_permissible_project(view=self)
        repo, _ = Repo.objects.get_or_create(project=project)
        return repo

    @staticmethod
    def _handle_posted_data(request, repo, directory):
        filename = os.path.join(directory, '{}.tar.gz'.format(repo.project.name))
        file_data = request.data['repo']

        # filename might already exist, if uploads are done in quick succession
        # we just delete the previous one and assume that its changes are already committed
        while os.path.exists(filename):
            os.remove(filename)

        # Creating the new file
        with open(filename, 'wb') as destination:
            for chunk in file_data.chunks():
                destination.write(chunk)
        return filename

    def put(self, request, *args, **kwargs):
        user = request.user
        repo = self.get_object()
        path = os.path.join(settings.UPLOAD_ROOT, user.username)
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            tar_file_name = self._handle_posted_data(request, repo, path)
        except (IOError, os.error) as e:  # pragma: no cover
            logger.warning(
                'IOError while trying to save posted data ({}): {}'.format(e.errno, e.strerror))
            return HttpResponseServerError()

        handle_new_files.delay(user_id=user.id,
                               repo_id=repo.id,
                               tar_file_name=tar_file_name)

        # do some stuff with uploaded file
        return Response(status=204)
