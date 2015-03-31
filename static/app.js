var app = app || {}

$(document).ready(function(){
    app.ready = true;

    app.updateLayout = function(response){
        var status = response['status'];
        if(status == 'ready'){
            app.commentToHtml(response['comment']);
        }
        else{
            app.setLoading();
        }
    }

    app.setLoading = function(){
        app.ready = false;
        $('#comment').attr('data-id', '');
        $('#comment #title').attr('href', '');
        $('#comment #title').text('Loading new comments...');
        var text = '<p>Welp, good work. We temporarily ran out of comments. ';
        text += 'Please come back later for more comments.</p>';
        $('#comment #text').html(text);
        $('#comment #author').attr('href', 'http://www.reddit.com/');
        $('#comment #author').text('Browse reddit');
    }

    app.commentToHtml = function(comment){
        app.ready = true;
        $('#comment').attr('data-id', comment['id']);
        $('#comment #title').attr('href', comment['permalink']);
        $('#comment #title').text(comment['title']);
        $('#comment #text').html(comment['comment_text']);
        $('#comment #author').attr('href', 'https://www.reddit.com/u/' + comment['comment_author']);
        $('#comment #author').text(comment['comment_author']);
    }

    app.getComment = function(){
        $.ajax({
            url: '/api/get_comment',
            method: 'GET',
            success: app.updateLayout,
            fail: app.setLoading,
        })
    }
    app.putComment = function(data){
        $.ajax({
            url: '/api/put_comment',
            method: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(data)
        }).always(app.getComment);
    }

    $('.button').click(function(e){
        if(!app.ready){
            app.getComment();
        }
        var data = {
            doc_class: $(this).attr("id") == 'is_review',
            comment_id: $('#comment').attr('data-id')
        }
        app.putComment(data);
    });

    if($('#comment').length > 0){
        app.getComment();
    }

});