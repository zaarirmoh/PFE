from rest_framework import serializers
from ..models.project_models import *


class ThemeRankingSerializer(serializers.ModelSerializer):
    theme_id = serializers.IntegerField(write_only=True)
    theme_title = serializers.CharField(source='theme.title', read_only=True)
    
    class Meta:
        model = ThemeRanking
        fields = ('theme_id', 'theme_title', 'rank')
        
class ThemeChoiceSerializer(serializers.ModelSerializer):
    rankings = ThemeRankingSerializer(source='themeranking_set', many=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = ThemeChoice
        fields = ('id', 'team', 'team_name', 'rankings', 'submission_date', 'is_final')
        read_only_fields = ('submission_date',)
    
    def validate_rankings(self, rankings):
        """Ensure rankings are consecutive and unique"""
        if not rankings:
            raise serializers.ValidationError("You must provide at least one theme choice")
        
        # Check for unique themes and ranks
        theme_ids = [r['theme_id'] for r in rankings]
        ranks = [r['rank'] for r in rankings]
        
        if len(set(theme_ids)) != len(theme_ids):
            raise serializers.ValidationError("Each theme can only be selected once")
            
        if len(set(ranks)) != len(ranks):
            raise serializers.ValidationError("Each rank can only be used once")
            
        # Check that ranks are consecutive starting from 1
        expected_ranks = list(range(1, len(rankings) + 1))
        if sorted(ranks) != expected_ranks:
            raise serializers.ValidationError("Ranks must be consecutive numbers starting from 1")
            
        return rankings
    
    def create(self, validated_data):
        rankings_data = validated_data.pop('themeranking_set')
        theme_choice = ThemeChoice.objects.create(**validated_data)
        
        # Create rankings
        for ranking_data in rankings_data:
            theme_id = ranking_data.pop('theme_id')
            ThemeRanking.objects.create(
                theme_choice=theme_choice,
                theme_id=theme_id,
                **ranking_data
            )
        
        return theme_choice
    
    def update(self, instance, validated_data):
        # Update the theme choice attributes
        instance.is_final = validated_data.get('is_final', instance.is_final)
        instance.save()
        
        # If there are new rankings, replace the old ones
        if 'themeranking_set' in validated_data:
            # Delete existing rankings
            instance.themeranking_set.all().delete()
            
            # Create new rankings
            rankings_data = validated_data.pop('themeranking_set')
            for ranking_data in rankings_data:
                theme_id = ranking_data.pop('theme_id')
                ThemeRanking.objects.create(
                    theme_choice=instance,
                    theme_id=theme_id,
                    **ranking_data
                )
        
        return instance

class ThemeAssignmentSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    theme_title = serializers.CharField(source='theme.title', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    
    class Meta:
        model = ThemeAssignment
        fields = ('id', 'team', 'team_name', 'theme', 'theme_title', 
                  'assigned_by', 'assigned_by_name', 'assigned_date', 'notes')
        read_only_fields = ('assigned_date', 'assigned_by')