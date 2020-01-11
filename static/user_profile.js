function display_post_box() {
    document.getElementById("post-register").style.display = "initial";
}

function display_comment_box(post_id) {
    document.getElementById("comment_post_id_" + post_id).style.display = "initial";
}

function changeEditableDescription() {
    description_div = document.getElementById("description");

    edit_button = document.getElementById("edit-button");
    edit_button.parentNode.removeChild(edit_button);

    description_content_div = document.getElementById("description-content");
    description = description_content_div.innerHTML;

    description = description.replace(/^\s+|\s+$/g, '');

    description_content_div.innerHTML = "";

    form = document.createElement("form");
    form.setAttribute('action', '/update_user');
    form.setAttribute('method', 'post');

    input = document.createElement("textarea");
    input.setAttribute("name", "description");
    input.setAttribute("rows", "3");
    input.setAttribute("cols", "35");
    input.innerHTML = description;

    sub = document.createElement("input");
    sub.setAttribute("type", "submit");
    sub.setAttribute("class", "btn-sm btn-primary")
    sub.setAttribute("value", "Submit");

    form.appendChild(input);
    form.appendChild(sub);

    description_content_div.appendChild(form);
}