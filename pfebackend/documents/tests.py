from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Teacher, Student
from teams.models import Team, TeamMembership
from documents.models import Document, DocumentType

class DocumentTests(TestCase):
    def setUp(self):
        # Create teacher with complete profile
        self.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            username='teachertest',
            password='pass123',
            first_name='Teacher',
            last_name='Test',
            user_type='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            department='Computer Science',
            grade='maitre_assistant_b'
        )

        # Create student with complete profile
        self.student_user = User.objects.create_user(
            email='student@test.com',
            username='studenttest',
            password='pass123',
            first_name='Student',
            last_name='Test',
            user_type='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            matricule='12345',
            enrollment_year=2023,
            current_year='4siw',
            academic_status='active'
        )

        # Create test file
        self.test_file = SimpleUploadedFile(
            "test_doc.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        # Create document
        self.document = Document.objects.create(
            title="Technical Documentation",
            file=self.test_file,
            document_type=DocumentType.TECHNICAL_SHEET
        )

    def test_document_creation(self):
        """Test document creation and basic attributes"""
        self.assertEqual(self.document.title, "Technical Documentation")
        self.assertEqual(self.document.document_type, DocumentType.TECHNICAL_SHEET)
        self.assertTrue(self.document.file)

    def test_document_string_representation(self):
        """Test string representation of document"""
        expected_str = f"Technical Documentation ({DocumentType.TECHNICAL_SHEET})"
        self.assertEqual(str(self.document), expected_str)

class DocumentAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create student with complete profile
        self.student_user = User.objects.create_user(
            email='student@test.com',
            username='studenttest',
            password='pass123',
            first_name='Student',
            last_name='Test',
            user_type='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            matricule='12345',
            enrollment_year=2023,
            current_year='4siw',
            academic_status='active'
        )
        
        # Create team
        self.team = Team.objects.create(
            name="Test Team",
            academic_year="4siw"
        )
        TeamMembership.objects.create(
            team=self.team,
            user=self.student_user,
            role=TeamMembership.ROLE_MEMBER
        )
        
        self.client.force_authenticate(user=self.student_user)
        
        # Create test file
        self.test_file = SimpleUploadedFile(
            "test_doc.pdf",
            b"file_content",
            content_type="application/pdf"
        )

    def test_document_upload_api(self):
        """Test document upload through API"""
        url = reverse('document-upload')
        data = {
            'title': 'API Test Document',
            'file': self.test_file,
            'document_type': DocumentType.TECHNICAL_SHEET
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)
        self.assertEqual(Document.objects.first().title, 'API Test Document')

    def test_document_list_api(self):
        """Test document listing endpoint"""
        # Create some documents first
        Document.objects.create(
            title="Document 1",
            file=self.test_file,
            document_type=DocumentType.TECHNICAL_SHEET
        )
        Document.objects.create(
            title="Document 2",
            file=self.test_file,
            document_type=DocumentType.LIVRABLE
        )

        url = reverse('document-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_document_download_api(self):
        """Test document download endpoint"""
        # Create a document first
        document = Document.objects.create(
            title="Download Test",
            file=self.test_file,
            document_type=DocumentType.TECHNICAL_SHEET
        )

        url = reverse('document-download', kwargs={'pk': document.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')
