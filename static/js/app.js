$.ajax({
    url: '/rooms/list',
    type: 'get',
    dataType: 'json',
    success: function (data) {
        $('.deleteBtn').each((i, elm) => {
            $(elm).on("click", (e) => {
                deleteRoom($(elm))
            })
        })
    }
});

function deleteColMissing(el) {
    roomId = $(el).data('id')
    $.ajax({
        url: `/rooms/delete/${roomId}`,
        type: 'post',
        dataType: 'json',
        success: function (data) {
            $(el).parents()[1].remove()
        }
    });
}