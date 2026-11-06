
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from .models import Business, BusinessMembership
from .utils import (
    get_current_business,
    get_current_membership,
    is_business_owner,
    require_business_owner,
)


User = get_user_model()


class BusinessMembershipTests(TestCase):

    def setUp(self):

        self.owner = User.objects.create_user(
            username="test_owner",
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.employee = User.objects.create_user(
            username="test_employee",
            email="employee@example.com",
            password="TestPassword123!",
        )

        self.business = Business.objects.create(
            name="Test Business",
        )

        self.owner_membership = (
            BusinessMembership.objects.create(
                user=self.owner,
                business=self.business,
                role=BusinessMembership.Role.OWNER,
            )
        )

        self.employee_membership = (
            BusinessMembership.objects.create(
                user=self.employee,
                business=self.business,
                role=BusinessMembership.Role.EMPLOYEE,
            )
        )

    def test_owner_business(self):

        self.assertEqual(
            get_current_business(self.owner),
            self.business,
        )

    def test_employee_business(self):

        self.assertEqual(
            get_current_business(self.employee),
            self.business,
        )

    def test_owner_role(self):

        self.assertTrue(
            is_business_owner(self.owner)
        )

    def test_employee_not_owner(self):

        self.assertFalse(
            is_business_owner(self.employee)
        )

    def test_owner_permission(self):

        self.assertEqual(
            require_business_owner(self.owner),
            self.business,
        )

    def test_employee_owner_permission_denied(self):

        with self.assertRaises(PermissionDenied):
            require_business_owner(self.employee)

    def test_inactive_membership_denied(self):

        self.employee_membership.is_active = False
        self.employee_membership.save()

        with self.assertRaises(PermissionDenied):
            get_current_membership(self.employee)

    def test_inactive_user_denied(self):

        self.employee.is_active = False
        self.employee.save()

        with self.assertRaises(PermissionDenied):
            get_current_business(self.employee)

    def test_multiple_active_businesses_denied(self):

        second_business = Business.objects.create(
            name="Second Business",
        )

        BusinessMembership.objects.create(
            user=self.owner,
            business=second_business,
            role=BusinessMembership.Role.OWNER,
        )

        with self.assertRaises(PermissionDenied):
            get_current_business(self.owner)
