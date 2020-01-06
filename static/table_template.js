function onChangeEntry(entry, field) {
    entry.style.backgroundColor = 'yellow';

    var input = document.createElement("input")
    input.name = "__" + field;
    input.value = entry.value;
    input.type = "hidden";
    var form = entry.parentElement.parentElement.getElementsByClassName("update")[0]
    form.getElementsByClassName("button")[0].disabled = false;
    form.appendChild(input);
}

function onChangeInsertEntry(entry) {
    entry.style.backgroundColor = 'yellow';

    var form = entry.parentElement.parentElement.getElementsByClassName('insert')[0]
    inputs = form.getElementsByTagName('input');
    var i;
    for (i = 0; i < inputs.length; ++i) {
        if (inputs[i].name == entry.name) {
            inputs[i].value = entry.value;
            break;
        }
    }
}

const $tableID = $('#table');

function onAddEntry(keys, table_name) {
    const $clone = $tableID.find('tbody tr').last().clone(true).removeClass('hide table-line');

    if ($tableID.find('tbody tr').length === 0) {
        /* <tr id="row_{{ entry[0] }}">
                {% for field in entry %}
                <th>
                    {% if info['keys'][loop.index - 1] != 'id' %}
                    <input class="form-control" name="{{ info['keys'][loop.index - 1] }}" value="{{ field }}"
                           onchange="onChangeEntry(this, '{{ info['keys'][loop.index - 1] }}')">
                    {% else %}
                    <input class="form-control" name="{{ info['keys'][loop.index - 1] }}" value="{{ field }}" disabled>
                    {% endif %}
                </th>
                {% endfor %}*/

        $row = $("<tr></tr>");

        for (i = 0; i < keys.length; ++i) {
            key = keys[i];

            $th = $("<th></th>");

            $input = $('<input></input>');
            $input.attr('name', key);
            if (key == 'id') {
                $input.attr('disabled', true);
                $input.attr('value', 1);
            } else {
                $input.attr('onchange', "onChangeInsertEntry(this);");
            }

            $input.addClass('form-control');
            $input.attr('name');

            $th.append($input);

            $row.append($th);
        }

        $th = $("<th></th>");

        $removeButton = $('<button/>',
        {
            text: 'Remove',
            class: 'remove btn btn-danger',
            click: function () {
               $(this).parents('tr').detach();
            }
        });
        $th.append($removeButton);
        $row.append($th);

        /*
        <th>
            <form class="update" action="/update/{{ table_name }}" method="post">
                <input class="button btn btn-warning" type="submit" value="Update" disabled>
                {% for key in info['keys'] %}
                <input type="hidden" name="{{ key }}" value="{{ entry[loop.index - 1] }}">
                {% endfor %}
            </form>
        </th>
        */
        $th = $("<th></th>");

        $form = $("<form></form>");
        $form.addClass('insert');
        $form.attr('action', '/insert/' + table_name);

        $input1 = $("<input></input>");
        $input1.addClass('button');
        $input1.addClass('btn');
        $input1.addClass('btn-primary');

        $input1.attr('type', 'submit');
        $input1.attr('value', 'Insert');

        $form.append($input1);

        var i;
        for (i = 0; i < keys.length; ++i) {
            key = keys[i];

            $input = $("<input></input>");
            $input.attr('type', 'hidden');
            $input.attr('name', key);
            if (key == 'id') {
                $input.attr('value', 1);
            } else {
                $input.attr('value', 'example');
            }

            $form.append($input);
        }

        $th.append($form);

        $row.append($th);

        $('tbody').append($row);
    } else {
        $clone.find('input').each(function (index) {
            if ($(this).attr('name') == 'id') {
                if ($(this).attr('type') == 'hidden') {
                    $(this).detach();
                } else {
                    old_value = $(this).attr('value')
                    console.log('Value: ' + old_value)
                    $(this).attr('value', parseInt(old_value) + 1);
                }
            }

            $(this).attr('onchange', 'onChangeInsertEntry(this);');
        });

        var removeButton = $('<button/>',
        {
            text: 'Remove',
            class: 'remove btn btn-danger',
            click: function () {
               $(this).parents('tr').detach();
            }
        });
        $clone.find('.delete').replaceWith(removeButton);

        $form = $clone.find('form').last();
        $form.attr('class', 'insert');

        var action = $form.attr('action');
        $form.attr('action', action.replace('update', 'insert'));

        $input = $form.find('.button').last();
        $input.attr('class', 'btn btn-primary');
        $input.attr('value', 'Insert');
        $input.attr('disabled', false);

        $tableID.find('table').append($clone);
    }
};