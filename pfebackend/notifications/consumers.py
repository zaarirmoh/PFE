# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Notification
from teams.models import *

class NotificationConsumer(AsyncWebsocketConsumer):
    
    
    async def connect(self):
        self.user = self.scope["user"]
        
        # Reject connection if user is not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Create a user-specific notification group
        self.notification_group_name = f"user_{self.user.id}_notifications"
        
        # Join the group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send any pending notifications
        await self.send_pending_notifications()
    
    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket (client to server)
    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command', None)
        
        if command == 'mark_read':
            notification_id = data.get('notification_id')
            success = await self.mark_notification_read(notification_id)
            
            await self.send(text_data=json.dumps({
                'type': 'notification_marked_read',
                'notification_id': notification_id,
                'success': success
            }))
        
        elif command == 'mark_all_read':
            count = await self.mark_all_notifications_read()
            
            await self.send(text_data=json.dumps({
                'type': 'all_notifications_marked_read',
                'count': count
            }))
            
        elif command == 'respond_to_invitation':
            invitation_id = data.get('invitation_id')
            response = data.get('response')  # 'accept' or 'decline'
            success, team_name = await self.process_invitation_response(invitation_id, response)
            
            await self.send(text_data=json.dumps({
                'type': 'invitation_response_processed',
                'invitation_id': invitation_id,
                'response': response,
                'success': success,
                'team_name': team_name
            }))
    
    # Receive message from notification group (server to client)
    async def notification_message(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.status = 'read'
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        count = Notification.objects.filter(
            recipient=self.user,
            status='unread'
        ).update(status='read')
        return count
    
    @database_sync_to_async
    def get_pending_notifications(self):
        
        # Get recent unread notifications
        notifications = Notification.objects.filter(
            recipient=self.user,
            status='unread'
        ).order_by('-created_at')[:10]
        
        # Convert to dictionary
        result = []
        for notification in notifications:
            notification_dict = {
                'id': notification.id,
                'content': notification.content,
                'type': notification.type,
                'created_at': notification.created_at.isoformat(),
                'priority': notification.priority,
                'action_url': notification.action_url,
            }
            result.append(notification_dict)
        
        return result
    
    async def send_pending_notifications(self):
        notifications = await self.get_pending_notifications()
        if notifications:
            await self.send(text_data=json.dumps({
                'type': 'pending_notifications',
                'notifications': notifications,
                'count': len(notifications)
            }))
            
    @database_sync_to_async
    def process_invitation_response(self, invitation_id, response):
        try:
            
            invitation = TeamInvitation.objects.get(
                id=invitation_id,
                invitee=self.user,
                status='pending'
            )
            
            if response == 'accept':
                invitation.status = 'accepted'
                invitation.save()
                
                # Add user to team
                TeamMembership.objects.create(
                    user=self.user,
                    team=invitation.team,
                    role='member'
                )
                
                return True, invitation.team.name
                
            elif response == 'decline':
                invitation.status = 'declined'
                invitation.save()
                return True, invitation.team.name
                
            return False, None
            
        except TeamInvitation.DoesNotExist:
            return False, None