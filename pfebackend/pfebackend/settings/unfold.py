from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "PFE PROJECT",
    "SITE_HEADER": "Platform gestion PFE",
    # "SITE_SUBHEADER": "Appears under SITE_HEADER",
    # "SITE_DROPDOWN": [
    #     {
    #         "icon": "diamond",
    #         "title": _("My site"),
    #         "link": "https://example.com",
    #     },
    #     # ...
    # ],
    "SITE_URL": "/",
    # "SITE_ICON": lambda request: static("icon.svg"),  # both modes, optimise for 32px height
    # "SITE_ICON": {
    #     "light": lambda request: static("icon-light.svg"),  # light mode
    #     "dark": lambda request: static("icon-dark.svg"),  # dark mode
    # },
    # "SITE_LOGO": lambda request: static("logo.svg"),  # both modes, optimise for 32px height
    # "SITE_LOGO": {
    #     "light": lambda request: static("logo-light.svg"),  # light mode
    #     "dark": lambda request: static("logo-dark.svg"),  # dark mode
    # },
    # "SITE_SYMBOL": "speed",  # symbol from icon set
    # "SITE_FAVICONS": [
    #     {
    #         "rel": "icon",
    #         "sizes": "32x32",
    #         "type": "image/svg+xml",
    #         "href": lambda request: static("favicon.svg"),
    #     },
    # ],
    "SHOW_HISTORY": True, # show/hide "History" button, default: True
    "SHOW_VIEW_ON_SITE": True, # show/hide "View on site" button, default: True
    "SHOW_BACK_BUTTON": False, # show/hide "Back" button on changeform in header, default: False
    # "ENVIRONMENT": "sample_app.environment_callback", # environment name in header
    # "ENVIRONMENT_TITLE_PREFIX": "sample_app.environment_title_prefix_callback", # environment name prefix in title tag
    # "DASHBOARD_CALLBACK": "sample_app.dashboard_callback",
    # "THEME": "dark", # Force theme: "dark" or "light". Will disable theme switcher
    # "LOGIN": {
    #     "image": lambda request: static("sample/login-bg.jpg"),
    #     "redirect_after": lambda request: reverse_lazy("admin:APP_MODEL_changelist"),
    # },
    # "STYLES": [
    #     lambda request: static("css/style.css"),
    # ],
    # "SCRIPTS": [
    #     lambda request: static("js/script.js"),
    # ],
    "BORDER_RADIUS": "6px",
    # "COLORS": {
    #     "base": {
    #         "50": "249 250 251",
    #         "100": "243 244 246",
    #         "200": "229 231 235",
    #         "300": "209 213 219",
    #         "400": "156 163 175",
    #         "500": "107 114 128",
    #         "600": "75 85 99",
    #         "700": "55 65 81",
    #         "800": "31 41 55",
    #         "900": "17 24 39",
    #         "950": "3 7 18",
    #     },
    #     "primary": {
    #         "50": "250 245 255",
    #         "100": "243 232 255",
    #         "200": "233 213 255",
    #         "300": "216 180 254",
    #         "400": "192 132 252",
    #         "500": "168 85 247",
    #         "600": "147 51 234",
    #         "700": "126 34 206",
    #         "800": "107 33 168",
    #         "900": "88 28 135",
    #         "950": "59 7 100",
    #     },
    #     "font": {
    #         "subtle-light": "var(--color-base-500)",  # text-base-500
    #         "subtle-dark": "var(--color-base-400)",  # text-base-400
    #         "default-light": "var(--color-base-600)",  # text-base-600
    #         "default-dark": "var(--color-base-300)",  # text-base-300
    #         "important-light": "var(--color-base-900)",  # text-base-900
    #         "important-dark": "var(--color-base-100)",  # text-base-100
    #     },
    # },
    "COLORS": {
        "base": {
            # Keep the original grayscale (or adjust if needed)
            "50": "247 249 253",   # Lightest shade (almost white with slight blue tint)
            "100": "240 244 250",
            "200": "225 233 243",
            "300": "204 217 235",
            "400": "153 173 204",
            "500": "107 134 172",
            "600": "75 99 140",
            "700": "50 70 110",
            "800": "31 45 79",
            "900": "17 26 50",     # Dark shade similar to your #092147
            "950": "5 10 30", 
        },
        "primary": {
            # New color palette using your brand colors
            "50": "237 243 251",   # Lightest shade of #97B2DE
            "100": "219 230 246",  
            "200": "189 208 238",  
            "300": "151 178 222",  # #97B2DE
            "400": "114 149 206",  
            "500": "77 119 189",   
            "600": "55 94 166",    
            "700": "26 72 142",    # #1A488E
            "800": "18 50 102",    
            "900": "9 33 71",      # #092147
            "950": "4 22 51",      # Darkest shade
        },
        "font": {
            # Keep existing font contrast settings (adjust if needed)
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-600)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },

    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "fr": "🇫🇷",
                "nl": "🇧🇪",
            },
        },
    },
    # "SIDEBAR": {
    #     "show_search": False,  # Search in applications and models names
    #     "show_all_applications": False,  # Dropdown with all applications and models
    #     "navigation": [
    #         {
    #             "title": _("Navigation"),
    #             "separator": True,  # Top border
    #             "collapsible": True,  # Collapsible group of links
    #             "items": [
    #                 {
    #                     "title": _("Dashboard"),
    #                     "icon": "dashboard",  # Supported icon set: https://fonts.google.com/icons
    #                     "link": reverse_lazy("admin:index"),
    #                     "badge": "sample_app.badge_callback",
    #                     "permission": lambda request: request.user.is_superuser,
    #                 },
    #                 {
    #                     "title": _("Users"),
    #                     "icon": "people",
    #                     "link": reverse_lazy("admin:auth_user_changelist"),
    #                 },
    #             ],
    #         },
    #     ],
    # },
    "TABS": [
        {
            "page": "timelines",
            "models": ["timelines.timeline"],
            "items": [
                # {
                #     "title": _("All timelines"),
                #     # "icon": "sports_motorsports",
                #     "link": lambda request: f"{reverse_lazy('admin:timelines_timeline_changelist')}",
                # },
                {
                    "title": _("2nd Year timelines"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:timelines_timeline_changelist')}?academic_year__exact=2",
                },
                {
                    "title": _("3rd Year timelines"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:timelines_timeline_changelist')}?academic_year__exact=3",
                },
                {
                    "title": _("4th Year SIW timelines"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:timelines_timeline_changelist')}?academic_year__exact=4siw",
                },
                {
                    "title": _("4th Year ISI timelines"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:timelines_timeline_changelist')}?academic_year__exact=4isi",
                },
                {
                    "title": _("4th Year IASD timelines"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:timelines_timeline_changelist')}?academic_year__exact=4iasd",
                },
                {
                    "title": _("5th Year SIW timelines"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:timelines_timeline_changelist')}?academic_year__exact=5siw",
                },
                {
                    "title": _("5th Year ISI timelines"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:timelines_timeline_changelist')}?academic_year__exact=5isi",
                },
                {
                    "title": _("5th Year IASD timelines"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:timelines_timeline_changelist')}?academic_year__exact=5iasd",
                },
            ],
        },
        {
            "page": "users",
            "models": ["users.user"],
            "items": [
                {
                    "title": _("Administrators"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:users_user_changelist')}?user_type__exact=administrator",
                },
                {
                    "title": _("Teachers"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:users_user_changelist')}?user_type__exact=teacher",
                },
                {
                    "title": _("Externals"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:users_user_changelist')}?user_type__exact=external",
                },
                {
                    "title": _("Students"),
                    # "icon": "sports_motorsports",
                    "link": lambda request: f"{reverse_lazy('admin:users_user_changelist')}?user_type__exact=student",
                },
            ],
        },
    ],
}


def dashboard_callback(request, context):
    """
    Callback to prepare custom variables for index template which is used as dashboard
    template. It can be overridden in application by creating custom admin/index.html.
    """
    context.update(
        {
            "sample": "example",  # this will be injected into templates/admin/index.html
        }
    )
    return context


def environment_callback(request):
    """
    Callback has to return a list of two values represeting text value and the color
    type of the label displayed in top right corner.
    """
    return ["Production", "danger"] # info, danger, warning, success


def badge_callback(request):
    return 3

def permission_callback(request):
    return request.user.has_perm("sample_app.change_model")