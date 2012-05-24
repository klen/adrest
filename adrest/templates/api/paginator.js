[
{% for obj in content.resources %}{% include emitter.get_template_path with content=obj %}{% if not forloop.last %}, {% endif %}{% endfor %}
]
