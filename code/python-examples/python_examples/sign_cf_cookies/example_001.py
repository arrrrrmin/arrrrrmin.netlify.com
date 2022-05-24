import aws_cdk as cdk
import aws_cdk.aws_s3 as aws_s3
import aws_cdk.aws_cognito as aws_cognito
import aws_cdk.aws_cloudfront as aws_cloudfront
from constructs import Construct


class InfraStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.main_bucket = aws_s3.Bucket(
            self,
            "MainBucket",
            bucket_name="main-bucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
        )

        self.main_bucket_oai = aws_cloudfront.S3OriginConfig(
            s3_bucket_source=self.main_bucket,
            origin_access_identity=aws_cloudfront.OriginAccessIdentity(
                self,
                "MainOAI",
                comment="OAI for Main S3 Bucket AccessDistro",
            ),
        )

        self.main_pool = aws_cognito.UserPool(
            self,
            "UserPool",
            user_pool_name="UserPool",
            self_sign_up_enabled=True,
            auto_verify=aws_cognito.AutoVerifiedAttrs(email=True),
            sign_in_aliases=aws_cognito.SignInAliases(username=True),
            user_verification=aws_cognito.UserVerificationConfig(
                email_subject="Verify your email for our awesome app!",
                email_body="Thanks for signing up to our awesome app! Your verification code is {####}",
                email_style=aws_cognito.VerificationEmailStyle.CODE,
            ),
            standard_attributes=aws_cognito.StandardAttributes(
                email=aws_cognito.StandardAttribute(required=True, mutable=True),
                family_name=aws_cognito.StandardAttribute(required=False, mutable=True),
                given_name=aws_cognito.StandardAttribute(required=False, mutable=True),
                # ...
            ),
            custom_attributes={
                "isAdmin": aws_cognito.BooleanAttribute(mutable=True),
                # ...
            },
            lambda_triggers=aws_cognito.UserPoolTriggers(
                post_confirmation=self.post_confirm_lambda_fn
            ),
        )

        self.main_pool.add_client(
            "WebAppClient",
            user_pool_client_name="WebAppClient",
            auth_flows=aws_cognito.AuthFlow(
                admin_user_password=True,
                user_password=True,
                user_srp=True,
            ),
            id_token_validity=cdk.Duration.minutes(60),
            generate_secret=True,
            o_auth=aws_cognito.OAuthSettings(
                flows=aws_cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[  # noqa
                    aws_cognito.OAuthScope.OPENID,
                    aws_cognito.OAuthScope.COGNITO_ADMIN,
                    aws_cognito.OAuthScope.EMAIL,
                ],
                callback_urls=["http://localhost:8000/v1/auth/verify/"],
                logout_urls=[],
            ),
            prevent_user_existence_errors=False,
            refresh_token_validity=cdk.Duration.days(30),
            # read_attributes (Default: All standard and custom attributes)
            # write_attributes (Default: All standard and custom attributes)
        )

        self.keygroup_public_key = aws_cloudfront.PublicKey(
            self,
            "CFPublicKeyCookieSigning",
            public_key_name="CFPublicKeyCookieSigning",
            encoded_key=open("/public_key.pem").read(),
        )
        self.keygroups = [
            aws_cloudfront.KeyGroup(
                self,
                "MainBucketAccessDistroKeyGroup",
                key_group_name="MainBucketAccessDistroKeyGroup",
                items=[self.keygroup_public_key],
            )
        ]
        self.access_distro = aws_cloudfront.CloudFrontWebDistribution(
            self,
            "MainAccessDistro",
            origin_configs=[
                aws_cloudfront.SourceConfiguration(
                    behaviors=[
                        aws_cloudfront.Behavior(
                            allowed_methods=aws_cloudfront.CloudFrontAllowedMethods.ALL,
                            is_default_behavior=True,
                            path_pattern="/",
                            trusted_key_groups=self.keygroups,
                            viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                        )
                    ],
                    s3_origin_source=self.main_bucket_oai,
                )
            ],
        )
