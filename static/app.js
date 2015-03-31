var app = app || {}

$(document).ready(function(){
    app.updateLayout = function(response){
        console.log('Updating Layout');
        var status = response['status'];
        if(status == 'ready'){
            app.commentToHtml(response['comment']);
        }
        else{
            app.setLoading();
        }
    }

    app.setLoading = function(){
        console.log('Application is Updating');
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
        console.log(comment)
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
            dataType: 'json'
        })
    }
    app.putComment = function(){

    }

    $('.button').click(function(e){
        app.getComment();
    });
});