function createAudioChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var audioTitle = chooserElement.find('.title');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).on('click', function() {
        ModalWorkflow({
            url: window.chooserUrls.audioChooser,
            onload: AUDIO_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                audioChosen: function(audioData) {
                    input.val(audioData.id);
                    audioTitle.text(audioData.title)
                    chooserElement.removeClass('blank');
                    editLink.attr('href', audioData.edit_link);
                }
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
