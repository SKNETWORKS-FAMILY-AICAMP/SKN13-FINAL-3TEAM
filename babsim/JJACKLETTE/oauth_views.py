from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import login
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialAccount
from .models import Users
import logging

logger = logging.getLogger(__name__)

def oauth_callback(request):
    """OAuth 콜백 처리 및 JWT 토큰 생성"""
    try:
        # OAuth 로그인 완료 후 사용자 정보를 직접 가져와서 Django 세션 설정
        
        # 현재 요청에서 OAuth 사용자 정보 확인
        from allauth.socialaccount.models import SocialAccount
        from django.contrib.auth import login
        
        # 방법 1: 가장 최근에 생성된 Google SocialAccount 확인
        try:
            latest_social_account = SocialAccount.objects.filter(
                provider='google'
            ).order_by('-date_joined').first()
            
            if latest_social_account:
                user = request.user
                
                # Django 세션에 사용자 로그인 (backend 명시)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                logger.info(f"User logged in via OAuth (latest account): {user.email}")
                
                # JWT 토큰 생성
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                
                # 세션에 JWT 토큰 정보 저장
                request.session['jwt_tokens'] = {
                    'user_id': str(user.user_id),
                    'email': user.email,
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
                
                logger.info(f"JWT tokens generated and stored in session for user: {user.email}")
                print(user)
                print(f"user_id: {user.user_id}")
                print(f"email: {user.email}")
                
                # .env 파일에 저장된 FRONTEND_URL 사용
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost')
                redirect_url = (
                    f"{frontend_url}/oauth-callback?"
                    f"access_token={access_token}&"
                    f"refresh_token={refresh_token}&"
                    f"user_id={user.user_id}&"
                    f"email={user.email}"
                )
                
                logger.info(f"Redirecting to frontend: {redirect_url}")
                return redirect(redirect_url)
            else:
                logger.warning("No Google SocialAccount found")
                return redirect('/login')
                
        except Exception as e:
            logger.error(f"Error getting latest social account: {e}")
            return redirect('/login')
        
    except Exception as e:
        logger.error(f"Error in oauth_callback: {e}")
        return redirect('/login')

def oauth_callback_authenticated(request):
    """이미 인증된 사용자에 대한 JWT 토큰 생성"""
    try:
        if request.user.is_authenticated:
            # JWT 토큰 생성
            refresh = RefreshToken.for_user(request.user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # 세션에 JWT 토큰 정보 저장
            request.session['jwt_tokens'] = {
                'user_id': str(request.user.user_id),
                'email': request.user.email,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            
            logger.info(f"JWT tokens generated for authenticated user: {request.user.email}")
            
            # .env 파일에 저장된 FRONTEND_URL 사용
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost')
            redirect_url = (
                f"{frontend_url}/oauth-callback?"
                f"access_token={access_token}&"
                f"refresh_token={refresh_token}&"
                f"user_id={request.user.user_id}&"
                f"email={request.user.email}"
            )
            
            logger.info(f"Redirecting to frontend: {redirect_url}")
            return redirect(redirect_url)
        else:
            logger.warning("User not authenticated in oauth_callback_authenticated")
            return redirect('/login')
            
    except Exception as e:
        logger.error(f"Error in oauth_callback_authenticated: {e}")
        return redirect('/login')

def generate_jwt_token(request):
    """현재 로그인된 사용자로부터 JWT 토큰 생성 API"""
    try:
        if request.user.is_authenticated:
            # JWT 토큰 생성
            refresh = RefreshToken.for_user(request.user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            logger.info(f"JWT tokens generated for user: {request.user.email}")
            
            return JsonResponse({
                'success': True,
                'user_id': str(request.user.user_id),
                'email': request.user.email,
                'access_token': access_token,
                'refresh_token': refresh_token
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
            
    except Exception as e:
        logger.error(f"Error generating JWT token: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def google_oauth_callback(request):
    """구글 OAuth 콜백 전용 처리"""
    return oauth_callback(request) 