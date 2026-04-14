"""
Secrets Manager - Sahool Yemen Platform
مدير الأسرار والمفاتيح
"""
import os
import time
import json
import base64
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Optional imports
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    ClientError = Exception

try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False


class SecretsManager:
    """Multi-provider secrets manager with caching"""

    def __init__(self, provider: str = 'env'):
        self.provider = provider
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        self.client = None

        self._initialize_client()

    def _initialize_client(self):
        """Initialize the secrets client based on provider"""
        if self.provider == 'aws' and HAS_BOTO3:
            try:
                self.client = boto3.session.Session().client(
                    service_name='secretsmanager',
                    region_name=os.getenv('AWS_REGION', 'us-east-1'),
                    endpoint_url=os.getenv('AWS_SECRETS_ENDPOINT'),
                )
                logger.info("AWS Secrets Manager client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS client: {e}")
                self.provider = 'env'

        elif self.provider == 'vault' and HAS_HVAC:
            try:
                self.client = hvac.Client(
                    url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
                    token=os.getenv('VAULT_TOKEN'),
                    verify=os.getenv('VAULT_VERIFY_SSL', 'true').lower() == 'true'
                )
                logger.info("HashiCorp Vault client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Vault client: {e}")
                self.provider = 'env'
        else:
            self.provider = 'env'
            logger.info("Using environment variables for secrets")

    def get_secret(self, secret_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get secret with caching"""
        cache_key = f"{secret_name}:{version or 'latest'}"

        # Check cache TTL
        if cache_key in self._cache_ttl:
            if self._cache_ttl[cache_key] > time.time():
                return self._cache.get(cache_key, {})

        try:
            secret = self._fetch_secret(secret_name, version)

            # Cache with TTL
            ttl = int(os.getenv('SECRET_CACHE_TTL', '3600'))
            self._cache[cache_key] = secret
            self._cache_ttl[cache_key] = time.time() + ttl

            logger.info(f"Secret retrieved: {secret_name}")
            return secret

        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            return self._fallback_to_env(secret_name)

    def _fetch_secret(self, secret_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Fetch secret from provider"""
        if self.provider == 'aws' and self.client:
            kwargs = {'SecretId': secret_name}
            if version:
                kwargs['VersionId'] = version

            response = self.client.get_secret_value(**kwargs)

            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                return json.loads(base64.b64decode(response['SecretBinary']))

        elif self.provider == 'vault' and self.client:
            mount_point = os.getenv('VAULT_MOUNT_POINT', 'secret')
            response = self.client.secrets.kv.v2.read_secret_version(
                path=secret_name,
                mount_point=mount_point
            )
            return response['data']['data']

        else:
            return self._fallback_to_env(secret_name)

    def _fallback_to_env(self, secret_name: str) -> Dict[str, Any]:
        """Fallback to environment variables"""
        env_name = secret_name.replace('-', '_').replace('/', '_').upper()
        env_value = os.getenv(env_name)

        if env_value:
            try:
                return json.loads(env_value)
            except json.JSONDecodeError:
                return {'value': env_value}

        logger.warning(f"No fallback for secret: {secret_name}")
        return {}

    def get_database_credentials(self, environment: str = 'production') -> Dict[str, str]:
        """Get database credentials"""
        secret_name = f"sahool/{environment}/database"
        secret = self.get_secret(secret_name)

        return {
            'host': secret.get('host', os.getenv('DB_HOST', 'localhost')),
            'port': str(secret.get('port', os.getenv('DB_PORT', '5432'))),
            'dbname': secret.get('dbname', os.getenv('DB_NAME', 'sahool')),
            'username': secret.get('username', os.getenv('DB_USER', 'postgres')),
            'password': secret.get('password', os.getenv('DB_PASS', '')),
        }

    def get_jwt_secrets(self, environment: str = 'production') -> Dict[str, str]:
        """Get JWT secrets"""
        secret_name = f"sahool/{environment}/jwt"
        secret = self.get_secret(secret_name)

        return {
            'secret_key': secret.get('secret_key', os.getenv('JWT_SECRET_KEY', '')),
            'algorithm': secret.get('algorithm', os.getenv('JWT_ALGORITHM', 'HS256')),
            'access_token_expire': secret.get('access_token_expire', os.getenv('JWT_ACCESS_EXPIRE', '30')),
        }

    def get_api_keys(self, service: str) -> Dict[str, str]:
        """Get API keys for external services"""
        secret_name = f"sahool/api-keys/{service}"
        secret = self.get_secret(secret_name)

        # Fallback to environment
        if not secret:
            env_prefix = service.upper().replace('-', '_')
            return {
                'api_key': os.getenv(f'{env_prefix}_API_KEY', ''),
                'api_secret': os.getenv(f'{env_prefix}_API_SECRET', ''),
            }

        return secret

    def get_redis_credentials(self) -> Dict[str, str]:
        """Get Redis credentials"""
        return {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': os.getenv('REDIS_PORT', '6379'),
            'password': os.getenv('REDIS_PASSWORD', ''),
            'db': os.getenv('REDIS_DB', '0'),
        }


# Global instance
def get_secrets_manager() -> SecretsManager:
    """Get or create global secrets manager instance"""
    provider = os.getenv('SECRETS_PROVIDER', 'env')
    return SecretsManager(provider=provider)

secrets_manager = get_secrets_manager()
