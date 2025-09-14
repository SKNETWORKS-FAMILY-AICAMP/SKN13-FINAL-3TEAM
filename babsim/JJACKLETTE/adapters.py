from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from .models import Users
import uuid


class CustomAccountAdapter(DefaultAccountAdapter):
    """일반 계정 생성 시 사용되는 어댑터"""
    
    def save_user(self, request, user, form, commit=True):
        """사용자 저장 시 user_id UUID 자동 생성"""
        if not user.user_id:
            user.user_id = uuid.uuid4()
        return super().save_user(request, user, form, commit)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """소셜 계정 생성 시 사용되는 어댑터"""
    
    def save_user(self, request, sociallogin, form=None):
        """소셜 로그인 시 사용자 저장"""
        user = super().save_user(request, sociallogin, form)
        
        # user_id가 없으면 UUID 생성
        if not user.user_id:
            user.user_id = uuid.uuid4()
            user.save()
        
        # Google에서 받은 정보로 사용자 정보 업데이트
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            
            # Google에서 받은 이름 정보로 user_name 설정
            if not user.user_name:
                user.user_name = extra_data.get('name', '')
            
            # Google에서 받은 프로필 이미지 설정
            if not user.profile_image:
                user.profile_image = extra_data.get('picture', '')
            
            user.save()
        
        return user
    
    def populate_user(self, request, sociallogin, data):
        """소셜 로그인 시 사용자 정보 채우기"""
        user = super().populate_user(request, sociallogin, data)
        
        # user_id UUID 자동 생성
        user.user_id = uuid.uuid4()
        
        # Google에서 받은 정보로 기본값 설정
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            user.user_name = extra_data.get('name', '')
            user.profile_image = extra_data.get('picture', '')
        
        return user
