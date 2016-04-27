from django import template

register = template.Library()


@register.inclusion_tag('recirc/video-recirc.html', takes_context=True)
def video_recirc_widget(context, source):
    context["source"] = source
    return context
