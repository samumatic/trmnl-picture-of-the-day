# frozen_string_literal: true

# This plugin's tests, run with `trmnlp test` (add `--report report` for a page of every screen it drew).
# Docs: https://github.com/usetrmnl/trmnlp#testing-plugins
RSpec.describe 'Picture of the Day' do
  def commons(image, caption)
    {
      'https://commons.wikimedia.org/w/api.php?*generator=images*' =>
        { json: JSON.parse(File.read(File.join(__dir__, "fixtures/#{image}.json"))) },
      'https://commons.wikimedia.org/w/api.php?*prop=revisions*' =>
        { json: JSON.parse(File.read(File.join(__dir__, "fixtures/#{caption}.json"))) }
    }
  end

  let(:custom_fields) { { 'language' => 'de' } }

  # Real Commons responses, captions in German and English.
  context 'with a tall picture (2026-10-12)' do
    let(:mocks) { commons('commons_image', 'commons_caption') }

    # Every view on TRMNL's devices, a failing API and every select option, checked for page errors and leaked values.
    it_behaves_like 'a publishable recipe'
  end

  context 'with a wide picture (2026-10-11)' do
    let(:mocks) { commons('commons_image_wide', 'commons_caption_wide') }

    it_behaves_like 'a publishable recipe'
  end
end
